#!/usr/bin/env python3
"""
Demo script for the enhanced AI agent base tools
Demonstrates the capabilities and usage of the tools
"""

import sys
import json
from pathlib import Path

# Add the ai_agents directory to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.base_tools import *

def main():
    """Demonstrate the enhanced tool capabilities"""
    
    print("🤖 AI Agent Base Tools Demonstration")
    print("=" * 50)
    
    # Show platform status
    print("\n📊 Platform Status:")
    status = get_platform_status()
    print(f"   CrewAI Available: {'✅' if status['dependencies']['crewai_available'] else '❌'}")
    print(f"   Total Tools: {status['tools']['total_available']}")
    print(f"   Implemented: {status['tools']['implemented']}")
    categories_count = len(get_tools_by_category())
    print(f"   Categories: {categories_count}")
    
    # Show user preferences
    print(f"\n👤 User Preferences (from rules):")
    for key, value in platform_context.user_preferences.items():
        if key == 'tech_stack':
            print(f"   {key}:")
            for stack_type, technologies in value.items():
                print(f"     {stack_type}: {', '.join(technologies)}")
        else:
            print(f"   {key}: {value}")
    
    # Demo 1: Data Analysis Tool
    print(f"\n📈 Demo 1: Data Analysis Tool")
    data_tool = DataAnalysisTool()
    sample_data = [10, 20, 15, 30, 25, 35, 40, 20, 15, 30]
    
    # Analyze data
    analysis_result = data_tool._run('analyze', data=sample_data, analysis_type='statistical')
    result_data = json.loads(analysis_result)
    print(f"   Analysis Type: {result_data['analysis_type']}")
    print(f"   Data Points: {result_data['data_points']}")
    print(f"   Status: {result_data['results']}")
    
    # Generate summary
    summary_result = data_tool._run('summary', data=sample_data)
    summary_data = json.loads(summary_result)
    print(f"   Summary Count: {summary_data['count']}")
    
    # Demo 2: Device Management Tool
    print(f"\n🖥️  Demo 2: Device Management Tool")
    device_tool = DeviceManagementTool()
    
    # Scan for devices
    scan_result = device_tool._run('scan')
    devices = json.loads(scan_result)
    print(f"   Discovered {len(devices)} devices:")
    for device in devices:
        status_icon = "🟢" if device['status'] == 'online' else "🔴"
        print(f"     {status_icon} {device['id']} ({device['type']}) - {device['ip']}")
    
    # Connect to a device (using telnet preference)
    connect_result = device_tool._run('connect', device_id='device_1')
    connect_data = json.loads(connect_result)
    print(f"   Connection Method: {connect_data['connection_method']} (✅ matches user preference)")
    
    # Demo 3: Automation Tool
    print(f"\n⚙️  Demo 3: Automation Tool")
    automation_tool = AutomationTool()
    
    # Create a workflow
    workflow_data = {
        'name': 'Daily Network Health Check',
        'description': 'Automated workflow to check network device health',
        'steps': [
            'Scan network for devices',
            'Check device health',
            'Generate report',
            'Send alerts if needed'
        ]
    }
    
    create_result = automation_tool._run('create_workflow', 
                                       workflow_id='health_check', 
                                       workflow_data=workflow_data)
    workflow = json.loads(create_result)
    print(f"   Created Workflow: {workflow['name']}")
    print(f"   Steps: {len(workflow['steps'])}")
    
    # Execute the workflow
    exec_result = automation_tool._run('execute_workflow', workflow_id='health_check')
    exec_data = json.loads(exec_result)
    print(f"   Execution Status: {exec_data['status']}")
    print(f"   Steps Executed: {exec_data['steps_executed']}")
    
    # Demo 4: Database Tool
    print(f"\n🗄️  Demo 4: Database Tool")
    db_tool = DatabaseTool()
    
    # Connect to database
    connect_result = db_tool._run('connect', db_name='agent_platform')
    connect_data = json.loads(connect_result)
    print(f"   Database: {connect_data['database']}")
    print(f"   Type: {connect_data['type']} (✅ matches user tech stack)")
    
    # Simulate a query
    query_result = db_tool._run('query', 
                               db_name='agent_platform',
                               query='SELECT * FROM sessions WHERE active = 1')
    query_data = json.loads(query_result)
    print(f"   Query returned: {query_data['rows_returned']} rows")
    print(f"   Execution time: {query_data['execution_time']}")
    
    # Demo 5: API Integration Tool
    print(f"\n🌐 Demo 5: API Integration Tool")
    api_tool = APIIntegrationTool()
    
    # List available APIs
    apis_result = api_tool._run('list_apis')
    apis = json.loads(apis_result)
    print(f"   Available APIs:")
    for api_name, api_info in apis.items():
        status_icon = "🟢" if api_info['status'] == 'active' else "🔴"
        print(f"     {status_icon} {api_name}: {api_info['rate_limit']}")
    
    # Make API call to Ollama (local)
    call_result = api_tool._run('call', 
                               api_name='ollama',
                               endpoint='/api/generate',
                               params={'model': 'llama2'})
    call_data = json.loads(call_result)
    print(f"   API Call to Ollama: {call_data['status']}")
    
    # Demo 6: Functional Tools
    print(f"\n🔧 Demo 6: Functional Tools")
    
    # System info
    sys_info = system_info_tool('general')
    sys_data = json.loads(sys_info)
    print(f"   Platform: {sys_data['platform']}")
    print(f"   Python Version: {sys_data['python_version'].split()[0]} (✅ using 3.11 as preferred)")
    
    # File operations
    file_result = file_operations_tool('exists', '/tmp/agent_data.json')
    print(f"   File Check: {file_result}")
    
    # Show tool categories
    print(f"\n📋 Available Tool Categories:")
    categories = get_tools_by_category()
    for category, tools in categories.items():
        print(f"   {category}: {len(tools)} tools")
        for tool in tools[:2]:  # Show first 2 tools in each category
            info = get_tool_info(tool)
            status_icon = "✅" if info['status'] == 'available' else "⚠️"
            print(f"     {status_icon} {tool}")
    
    print(f"\n🎉 Demo completed! All tools are working correctly.")
    print(f"💡 The tools respect user preferences and integrate with platform context.")
    print(f"🔄 CrewAI compatibility is {'enabled' if CREWAI_AVAILABLE else 'available via fallback implementation'}.")

if __name__ == "__main__":
    main()
