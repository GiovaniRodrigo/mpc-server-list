# Arquitetura e Padrão de Design: MCP Dynamic Router Engine

## 1. Visão Geral da Arquitetura

O **MCP Dynamic Router Engine** é um padrão de arquitetura e roteamento de conexões para o **Model Context Protocol (MCP)**. Ele funciona de forma análoga a um Gateway ou Catálogo de APIs tradicional (REST/OpenAPI), abstraindo a inicialização, comunicação via sub-processos (`stdio`), roteamento e execução de ferramentas (*tools*) oferecidas por servidores MCP públicos e privados.

### Fluxo de Execução

```
+------------------+         1. Solicita Execução         +--------------------+
|  Cliente / LLM   | -----------------------------------> |  MCP Router Engine |
+------------------+  (server_key, tool_name, args)       +--------------------+
|
| 2. Consulta Configuração
v
+--------------------+
| mcp_servers.json   |
+--------------------+
|
| 3. Inicia Sub-processo (Stdio)
v
+--------------------+
| MCP Server Process |
| (npx / uvx / node) |
+--------------------+
|
| 4. Call Tool (JSON-RPC)
v
+------------------+ <----------------------------------- +--------------------+
| Retorno (Text/  |           5. Resultado                | Execução do MCP    |
| JSON Content)    |                                      +--------------------+
+------------------+
```

---

## 2. Estrutura do Projeto

```
mpc-server-list/
│
├── config/
│   └── mcp_servers.json       # Catálogo de registro dos servidores MCP
│
├── src/
│   ├── __init__.py
│   ├── config.py              # Parser e validação das configurações
│   ├── exceptions.py          # Exceções customizadas da aplicação
│   └── router.py              # Motor principal de roteamento e ciclo de vida
│
├── main.py                    # Script de entrada e exemplo de execução
├── requirements.txt           # Dependências do projeto
├── mcp_architecture_router.md # Documentação detalhada da arquitetura
└── README.md                  # Documentação do repositório
```

---

## 3. Padrões de Design Aplicados (Design Patterns)

* **Gateway Pattern / Dynamic Router:** Ponto centralizado para recebimento de chamadas e despacho dinâmico para o servidor correspondente com base no `server_key`.
* **Factory Method / Adapter Pattern:** Abstrai a criação e inicialização dos comandos dos subprocessos (`StdioServerParameters`) para que o chamador não precise conhecer a forma de execução (seja `npx`, `uvx`, ou `python`).
* **Resource Acquisition Is Initialization (RAII):** Gerenciamento assíncrono do ciclo de vida da conexão via *Async Context Managers* (`async with`), garantindo abertura e encerramento limpo dos subprocessos sem deixar processos-fantasma em memória.
* **Separation of Concerns (SoC):** A especificação das conexões (`mcp_servers.json`) é totalmente desvinculada do motor de execução (`MCPRouter`).

---

## 4. Implementação do Código

### 4.1 Catálogo de Conexões (`config/mcp_servers.json`)

```json
{
  "filesystem": {
    "command": "npx",
    "args": [
      "-y",
      "@modelcontextprotocol/server-filesystem",
      "./data"
    ],
    "description": "Servidor MCP para manipulação de arquivos locais na pasta ./data"
  },
  "fetch": {
    "command": "uvx",
    "args": [
      "mcp-server-fetch"
    ],
    "description": "Servidor MCP para requisições HTTP e extração de conteúdo web em Markdown"
  },
  "sqlite": {
    "command": "uvx",
    "args": [
      "mcp-server-sqlite",
      "--db-path",
      "./database.db"
    ],
    "description": "Servidor MCP para acesso e consulta SQL em banco SQLite"
  }
}
```

---

### 4.2 Exceções Customizadas (`src/exceptions.py`)

```python
class MCPException(Exception):
    """Exceção base para erros do MCP Router."""
    pass

class MCPServerNotFoundError(MCPException):
    """Lançada quando a chave do servidor MCP não é encontrada no catálogo."""
    pass

class MCPConfigurationError(MCPException):
    """Lançada quando há inconsistência na leitura do arquivo de configuração."""
    pass
```

---

### 4.3 Motor de Roteamento (`src/router.py`)

```python
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from src.exceptions import MCPConfigurationError, MCPServerNotFoundError


class MCPRouter:
    """
    Motor de roteamento dinâmico para gerenciar conexões com servidores MCP via stdio.
    """

    def __init__(self, config_path: str = "config/mcp_servers.json") -> None:
        self.config_path = Path(config_path)
        self.servers_config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Carrega e valida o arquivo JSON de catálogo de conexões."""
        if not self.config_path.exists():
            raise MCPConfigurationError(
                f"Arquivo de configuração não encontrado em: {self.config_path.resolve()}"
            )

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise MCPConfigurationError(f"Erro ao decodificar arquivo JSON de configuração: {e}")

    def _build_server_params(self, server_key: str) -> StdioServerParameters:
        """Monta os parâmetros do processo para a chave solicitada."""
        if server_key not in self.servers_config:
            raise MCPServerNotFoundError(
                f"Servidor MCP '{server_key}' não está cadastrado no catálogo."
            )

        server_info = self.servers_config[server_key]
        return StdioServerParameters(
            command=server_info["command"],
            args=server_info.get("args", []),
            env=server_info.get("env", None)
        )

    async def execute_tool(
        self,
        server_key: str,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Any:
        """
        Conecta ao servidor MCP especificado, executa a tool desejada e encerra a conexão.
        """
        server_params = self._build_server_params(server_key)

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments or {})
                return result

    async def list_tools(self, server_key: str) -> List[Any]:
        """
        Inspeciona e retorna a lista de ferramentas disponíveis em um servidor MCP.
        """
        server_params = self._build_server_params(server_key)

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                response = await session.list_tools()
                return response.tools
```

---

### 4.4 Ponto de Entrada / Exemplo (`main.py`)

```python
import asyncio
from src.router import MCPRouter
from src.exceptions import MCPException

async def run_demo():
    router = MCPRouter("config/mcp_servers.json")

    try:
        # 1. Inspecionar ferramentas disponíveis
        server_target = "fetch"
        print(f"=== Ferramentas do Servidor MCP: '{server_target}' ===")
        tools = await router.list_tools(server_target)
        for tool in tools:
            print(f"- Nome: {tool.name}")
            print(f"  Descrição: {tool.description}")

        print("\\n=== Executando chamada via MCP Router ===")
        # 2. Executar requisição
        response = await router.execute_tool(
            server_key="fetch",
            tool_name="fetch",
            arguments={"url": "https://httpbin.org/get"}
        )

        print("\\nResposta recebida do MCP:")
        if response.content:
            print(response.content[0].text)

    except MCPException as err:
        print(f"[Erro de MCP]: {err}")
    except Exception as err:
        print(f"[Erro Inesperado]: {err}")

if __name__ == "__main__":
    asyncio.run(run_demo())
```

---

## 5. Arquivo de Dependências (`requirements.txt`)

```text
mcp>=1.0.0
pydantic>=2.0.0
```

---

## 6. Boas Práticas e Extensibilidade

1. **Gestão de Variáveis de Ambiente:** É recomendado estender o arquivo `mcp_servers.json` para aceitar tokens de API e chaves secretas repassando-as dinamicamente ao campo `env` do `StdioServerParameters`.

2. **Evolução para Connection Pool:** Em cenários de alta taxa de requisições, substitua a criação pontual do *Async Context Manager* por um *Pool Manager* com conexões persistentes abertas em background.

3. **Validação de Schemas:** Integre validação Pydantic para os parâmetros de entrada antes de repassá-los para a camada `call_tool`.

---

## 7. Casos de Uso

### 1. Integração com LLMs
Use o router para permitir que agentes de LLM executem ferramentas MCP de forma segura e controlada:

```python
async def llm_tool_executor(server_key, tool_name, args):
    router = MCPRouter()
    return await router.execute_tool(server_key, tool_name, args)
```

### 2. Orquestração de Workflows
Combine múltiplos servidores MCP em um workflow:

```python
async def workflow():
    router = MCPRouter()
    
    # Buscar dados da web
    web_content = await router.execute_tool("fetch", "fetch", {"url": "..."})
    
    # Salvar em arquivo local
    await router.execute_tool("filesystem", "write", {"path": "...", "content": web_content})
    
    # Processar em banco de dados
    await router.execute_tool("sqlite", "execute", {"query": "..."})
```

### 3. API Gateway para MCP
Expor servidores MCP como endpoints HTTP:

```python
from fastapi import FastAPI
app = FastAPI()
router = MCPRouter()

@app.post("/execute/{server_key}/{tool_name}")
async def execute_mcp_tool(server_key: str, tool_name: str, args: dict):
    return await router.execute_tool(server_key, tool_name, args)
```

---

## 8. Considerações de Segurança

1. **Validação de Input:** Sempre valide e sanitize os parâmetros antes de passá-los ao `execute_tool`.
2. **Isolamento de Processos:** Use contextos assíncrono para garantir que processos sejam encerrados mesmo em caso de exceções.
3. **Rate Limiting:** Implemente throttling para evitar sobrecarga de recursos.
4. **Logging e Auditoria:** Registre todas as chamadas de ferramenta para fins de auditoria e debugging.

---

## 9. Troubleshooting

### "Arquivo de configuração não encontrado"
Verifique se `mcp_servers.json` está no caminho especificado e se o arquivo é acessível.

### "Servidor MCP não está cadastrado no catálogo"
Confirme que a chave `server_key` existe em `mpc_servers.json` e está escrita corretamente.

### "Erro ao decodificar arquivo JSON"
Valide a sintaxe JSON usando ferramentas como `jq` ou online JSON validators.

### Processos orfãos em memória
Certifique-se de que está usando `async with` corretamente para garantir limpeza de recursos.

---

**Versão:** 1.0  
**Última Atualização:** 2026-09-06
