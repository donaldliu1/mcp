import logging
from strands import Agent
from strands_tools import shell
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

logging.basicConfig(
   filename='agent_thinking.log',
   level=logging.INFO,
   format='%(asctime)s - %(message)s'
)
logger = logging.getLogger("my_agent")

tool_use_ids = []
text_buffer = []

def callback_handler(**kwargs):
    if "data" in kwargs:
        text_buffer.append(kwargs["data"])
    elif "current_tool_use" in kwargs:
        tool = kwargs["current_tool_use"]
        if tool["toolUseId"] not in tool_use_ids:
            logger.info(f"[Using tool: {tool.get('name')}]")
            tool_use_ids.append(tool["toolUseId"])

local_postgres_mcp = MCPClient(
   lambda: stdio_client(StdioServerParameters(
      command="python3", 
      args=["-m", "awslabs.postgres_mcp_server.server", "--allow_write_query"], 
      cwd="/Users/dzhl/Documents/awslabs/mcp/src/postgres-mcp-server",
      env={
            "AWS_PROFILE": "default",
            "AWS_REGION": "us-east-1",
            "FASTMCP_LOG_LEVEL": "ERROR",
            "PYTHONPATH": "/Users/dzhl/Documents/awslabs/mcp/src/postgres-mcp-server"
      }
   ))
)


with local_postgres_mcp:
   mcp_agent = Agent(tools=local_postgres_mcp.list_tools_sync(), callback_handler=callback_handler)
   print("patched local postgres MCP tools loaded")
   while True:
      try:
            user_input = input("").strip()
            
            if user_input.lower() == 'exit':
               print("Exiting...")
               break
            if not user_input:
               continue
            
            text_buffer.clear()
            response = mcp_agent(user_input)
            
            if text_buffer:
               logger.info(f"\nUser: {user_input}")
               logger.info(f"Agent thinking: {''.join(text_buffer)}\n")
            
            print(f"\n{response.message['content'][0]['text']}\n")
            
      except KeyboardInterrupt:
            print("\n\nInterrupted. Exiting...")
            break
      except Exception as e:
            print(f"Error: {e}")
            continue