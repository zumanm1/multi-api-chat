"""
AI Agents Configuration
Defines agent roles, capabilities, and system-wide settings for the Multi-API Chat Platform
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
import os

@dataclass
class AgentConfig:
    """Configuration for individual AI agents"""
    name: str
    role: str
    goal: str
    backstory: str
    capabilities: List[str]
    memory: bool = True
    verbose: bool = True
    max_execution_time: Optional[int] = None
    tools: List[str] = None
    llm_config: Dict = None

    def __post_init__(self):
        if self.tools is None:
            self.tools = []
        if self.llm_config is None:
            self.llm_config = {}

class AgentsConfig:
    """Central configuration for all AI agents in the system"""
    
    def __init__(self):
        self.enabled = os.getenv('AI_AGENTS_ENABLED', 'true').lower() == 'true'
        self.debug_mode = os.getenv('AI_AGENTS_DEBUG', 'false').lower() == 'true'
        self.default_llm = os.getenv('AI_AGENTS_DEFAULT_LLM', 'gpt-4')
        self.max_concurrent_tasks = int(os.getenv('AI_AGENTS_MAX_CONCURRENT', '3'))
        
        # Agent configurations
        self.agents = self._define_agents()
        
    def _define_agents(self) -> Dict[str, AgentConfig]:
        """Define all AI agents and their configurations"""
        
        agents = {
            # Master AI Agent - Orchestrator
            "master_agent": AgentConfig(
                name="Master AI Agent",
                role="AI System Orchestrator",
                goal="Coordinate and manage all AI agents across the platform to provide seamless user experience",
                backstory="""You are the Master AI Agent, the central intelligence that orchestrates 
                all other AI agents in the Multi-API Chat Platform. You understand user intentions, 
                delegate tasks to specialized agents, and ensure coherent responses across all platform features. 
                You maintain context awareness across different pages and coordinate cross-functional operations.""",
                capabilities=[
                    "task_delegation",
                    "context_management", 
                    "cross_agent_coordination",
                    "user_intent_analysis",
                    "response_synthesis",
                    "error_handling",
                    "performance_monitoring"
                ],
                tools=["user_context_tool", "agent_communication_tool", "task_scheduler_tool"],
                llm_config={"temperature": 0.7, "max_tokens": 2000}
            ),
            
            # Chat Agent - Main conversational interface
            "chat_agent": AgentConfig(
                name="Chat Agent", 
                role="Conversational Assistant",
                goal="Provide intelligent conversational responses and manage chat interactions",
                backstory="""You are the Chat Agent, specializing in natural language conversations. 
                You handle user queries, provide helpful responses, and can intelligently route complex 
                requests to other specialized agents. You maintain conversation context and ensure 
                engaging user interactions.""",
                capabilities=[
                    "natural_language_processing",
                    "conversation_management",
                    "context_retention",
                    "multi_api_integration",
                    "response_optimization",
                    "user_preference_learning"
                ],
                tools=["chat_history_tool", "api_integration_tool", "context_memory_tool"],
                llm_config={"temperature": 0.8, "max_tokens": 1500}
            ),
            
            # Analytics Agent - Data analysis and insights
            "analytics_agent": AgentConfig(
                name="Analytics Agent",
                role="Data Analyst and Insights Generator", 
                goal="Analyze platform usage data and provide actionable insights",
                backstory="""You are the Analytics Agent, an expert in data analysis and visualization. 
                You monitor platform metrics, identify trends, generate reports, and provide predictive 
                insights to optimize system performance and user experience.""",
                capabilities=[
                    "data_analysis",
                    "pattern_recognition", 
                    "predictive_modeling",
                    "report_generation",
                    "visualization_creation",
                    "performance_monitoring",
                    "anomaly_detection"
                ],
                tools=["data_analysis_tool", "chart_generator_tool", "metrics_collector_tool"],
                llm_config={"temperature": 0.3, "max_tokens": 1200}
            ),
            
            # Device Management Agent
            "device_agent": AgentConfig(
                name="Device Management Agent",
                role="IoT Device Manager",
                goal="Monitor and manage connected devices and IoT infrastructure",
                backstory="""You are the Device Management Agent, responsible for overseeing all 
                connected devices and IoT systems. You monitor device health, manage configurations, 
                troubleshoot issues, and ensure optimal device performance.""",
                capabilities=[
                    "device_monitoring",
                    "configuration_management",
                    "health_diagnostics", 
                    "automatic_remediation",
                    "security_monitoring",
                    "firmware_management",
                    "network_optimization"
                ],
                tools=["device_scanner_tool", "config_manager_tool", "health_monitor_tool"],
                llm_config={"temperature": 0.4, "max_tokens": 1000}
            ),
            
            # Operations Agent
            "operations_agent": AgentConfig(
                name="Operations Agent", 
                role="System Operations Manager",
                goal="Manage system operations, monitoring, and maintenance tasks",
                backstory="""You are the Operations Agent, ensuring smooth system operations. 
                You monitor system health, manage deployments, handle incidents, and maintain 
                system reliability and performance.""",
                capabilities=[
                    "system_monitoring",
                    "incident_management",
                    "deployment_automation",
                    "log_analysis",
                    "alerting_management", 
                    "capacity_planning",
                    "backup_management"
                ],
                tools=["system_monitor_tool", "log_analyzer_tool", "alert_manager_tool"],
                llm_config={"temperature": 0.2, "max_tokens": 1000}
            ),
            
            # Automation Agent  
            "automation_agent": AgentConfig(
                name="Automation Agent",
                role="Workflow Automation Specialist", 
                goal="Create, manage, and execute automated workflows and processes",
                backstory="""You are the Automation Agent, expert in creating and managing automated 
                workflows. You design efficient processes, trigger automated responses, and optimize 
                repetitive tasks across the platform.""",
                capabilities=[
                    "workflow_design",
                    "process_automation",
                    "trigger_management", 
                    "schedule_optimization",
                    "rule_engine_management",
                    "integration_orchestration",
                    "performance_optimization"
                ],
                tools=["workflow_builder_tool", "scheduler_tool", "trigger_manager_tool"], 
                llm_config={"temperature": 0.5, "max_tokens": 1200}
            ),
            
            # Backend AI Agent
            "backend_agent": AgentConfig(
                name="Backend AI Agent",
                role="Backend Systems Intelligence",
                goal="Manage backend operations, API integrations, and system intelligence",
                backstory="""You are the Backend AI Agent, the intelligence behind all backend 
                operations. You manage API integrations, optimize database queries, handle system 
                logic, and ensure backend efficiency and reliability.""",
                capabilities=[
                    "api_management",
                    "database_optimization",
                    "system_integration",
                    "performance_tuning",
                    "security_enforcement",
                    "data_processing",
                    "service_orchestration"
                ],
                tools=["api_manager_tool", "db_optimizer_tool", "security_scanner_tool"],
                llm_config={"temperature": 0.3, "max_tokens": 1500}
            )
        }
        
        return agents
    
    def get_agent_config(self, agent_name: str) -> Optional[AgentConfig]:
        """Get configuration for a specific agent"""
        return self.agents.get(agent_name)
    
    def get_all_agents(self) -> Dict[str, AgentConfig]:
        """Get all agent configurations"""
        return self.agents
    
    def is_agent_enabled(self, agent_name: str) -> bool:
        """Check if a specific agent is enabled"""
        return self.enabled and agent_name in self.agents

# Global instance
AGENTS_CONFIG = AgentsConfig()
