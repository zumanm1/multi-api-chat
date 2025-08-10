#!/usr/bin/env python3
"""
Advanced Multi-Agent Workflow Orchestrator
==========================================

This module provides sophisticated orchestration for complex multi-agent workflows,
including dependency management, parallel execution, error recovery, and performance optimization.

Features:
- Complex workflow definition and execution
- Agent dependency management
- Parallel and sequential task execution
- Error recovery and rollback mechanisms
- Performance monitoring and optimization
- Workflow visualization and analytics
"""

import asyncio
import logging
import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
import threading
from concurrent.futures import ThreadPoolExecutor, Future

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running" 
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class WorkflowTask:
    """Individual task in a workflow"""
    id: str
    name: str
    agent_type: str
    payload: Dict[str, Any]
    priority: TaskPriority = TaskPriority.MEDIUM
    dependencies: List[str] = field(default_factory=list)
    timeout: float = 30.0
    retry_count: int = 3
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    execution_time: float = 0.0

@dataclass 
class WorkflowDefinition:
    """Complete workflow definition"""
    id: str
    name: str
    description: str
    tasks: List[WorkflowTask]
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    max_parallel: int = 5
    timeout: float = 300.0  # 5 minutes default

class WorkflowOrchestrator:
    """Advanced workflow orchestration engine"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.active_workflows: Dict[str, WorkflowDefinition] = {}
        self.workflow_status: Dict[str, Dict[str, Any]] = {}
        self.agent_processors: Dict[str, Callable] = {}
        self.performance_metrics: Dict[str, List[float]] = {
            'execution_times': [],
            'success_rates': [],
            'parallel_efficiency': []
        }
        
        # Register default agent processors
        self._register_default_processors()
        
    def _register_default_processors(self):
        """Register default agent processors using simple master agent"""
        try:
            # Import simple master agent directly
            import sys
            import os
            agents_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'agents')
            if agents_path not in sys.path:
                sys.path.insert(0, agents_path)
            from simple_master_agent import get_simple_master_agent
            
            # Create processor that uses simple master agent
            def create_master_agent_processor(agent_type):
                def processor(payload):
                    import asyncio
                    
                    # Get master agent
                    master_agent = get_simple_master_agent()
                    
                    # Add agent type hint to context
                    context = payload.get('context', {})
                    context['preferred_agent'] = agent_type
                    
                    # Run async request
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(
                            master_agent.process_user_request(
                                request=payload.get('message', ''),
                                context=context,
                                source_page='workflow'
                            )
                        )
                        return result
                    finally:
                        loop.close()
                
                return processor
            
            # Register processors for each agent type
            agent_types = ['chat', 'analytics', 'device', 'operations', 'automation']
            for agent_type in agent_types:
                self.agent_processors[agent_type] = create_master_agent_processor(agent_type)
                
            logger.info("Registered master agent processors for workflow execution")
            
        except ImportError as e:
            # Fallback to demo mode processors if integration module not available
            logger.warning(f"Master agent not available ({e}), using demo processors")
            
            def create_demo_processor(agent_type):
                def demo_processor(payload):
                    import time
                    import random
                    
                    time.sleep(random.uniform(0.5, 2.0))  # Simulate processing time
                    
                    return {
                        "agent_type": agent_type,
                        "status": "success",
                        "response": f"Demo {agent_type} agent processed: {payload.get('message', 'No message')}",
                        "timestamp": time.time(),
                        "demo_mode": True
                    }
                return demo_processor
            
            # Register demo processors
            agent_types = ['chat', 'analytics', 'device', 'operations', 'automation']
            for agent_type in agent_types:
                self.agent_processors[agent_type] = create_demo_processor(agent_type)
    
    def register_agent_processor(self, agent_type: str, processor: Callable):
        """Register a custom agent processor"""
        self.agent_processors[agent_type] = processor
        logger.info(f"Registered processor for agent type: {agent_type}")
    
    def create_workflow(self, definition: WorkflowDefinition) -> str:
        """Create a new workflow"""
        workflow_id = definition.id
        self.active_workflows[workflow_id] = definition
        self.workflow_status[workflow_id] = {
            'status': 'created',
            'progress': 0.0,
            'tasks_completed': 0,
            'tasks_total': len(definition.tasks),
            'start_time': None,
            'estimated_completion': None,
            'errors': []
        }
        
        logger.info(f"Created workflow: {workflow_id} with {len(definition.tasks)} tasks")
        return workflow_id
    
    async def execute_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Execute a workflow with advanced orchestration"""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        workflow = self.active_workflows[workflow_id]
        status = self.workflow_status[workflow_id]
        
        # Update status
        status['status'] = 'running'
        status['start_time'] = datetime.now()
        
        logger.info(f"Starting workflow execution: {workflow_id}")
        
        try:
            # Build dependency graph
            dependency_graph = self._build_dependency_graph(workflow.tasks)
            
            # Execute tasks with dependency management
            results = await self._execute_with_dependencies(
                workflow.tasks, 
                dependency_graph, 
                workflow.max_parallel,
                workflow.timeout
            )
            
            # Calculate performance metrics
            self._update_performance_metrics(workflow, results)
            
            # Update final status
            status['status'] = 'completed'
            status['progress'] = 1.0
            status['end_time'] = datetime.now()
            status['results'] = results
            
            logger.info(f"Workflow completed successfully: {workflow_id}")
            
            return {
                'workflow_id': workflow_id,
                'status': 'success',
                'results': results,
                'execution_time': (status['end_time'] - status['start_time']).total_seconds(),
                'tasks_completed': len(results),
                'performance_metrics': self._get_workflow_metrics(workflow_id)
            }
            
        except Exception as e:
            status['status'] = 'failed'
            status['error'] = str(e)
            status['end_time'] = datetime.now()
            
            logger.error(f"Workflow execution failed: {workflow_id}, Error: {e}")
            
            return {
                'workflow_id': workflow_id,
                'status': 'failed',
                'error': str(e),
                'execution_time': (status['end_time'] - status['start_time']).total_seconds() if status['start_time'] else 0,
                'tasks_completed': status['tasks_completed']
            }
    
    def _build_dependency_graph(self, tasks: List[WorkflowTask]) -> Dict[str, Set[str]]:
        """Build task dependency graph"""
        graph = {}
        task_ids = {task.id for task in tasks}
        
        for task in tasks:
            # Validate dependencies exist
            invalid_deps = set(task.dependencies) - task_ids
            if invalid_deps:
                raise ValueError(f"Task {task.id} has invalid dependencies: {invalid_deps}")
            
            graph[task.id] = set(task.dependencies)
        
        # Check for circular dependencies
        self._check_circular_dependencies(graph)
        
        return graph
    
    def _check_circular_dependencies(self, graph: Dict[str, Set[str]]):
        """Check for circular dependencies in the workflow"""
        def has_cycle(node, visited, rec_stack):
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor, visited, rec_stack):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        visited = set()
        for node in graph:
            if node not in visited:
                if has_cycle(node, visited, set()):
                    raise ValueError(f"Circular dependency detected in workflow")
    
    async def _execute_with_dependencies(self, tasks: List[WorkflowTask], 
                                       dependency_graph: Dict[str, Set[str]],
                                       max_parallel: int, timeout: float) -> Dict[str, Any]:
        """Execute tasks with dependency management"""
        task_map = {task.id: task for task in tasks}
        completed_tasks = set()
        running_tasks = {}
        results = {}
        
        start_time = time.time()
        
        while len(completed_tasks) < len(tasks):
            # Check timeout
            if time.time() - start_time > timeout:
                raise TimeoutError(f"Workflow execution timeout after {timeout} seconds")
            
            # Find ready tasks (dependencies completed)
            ready_tasks = []
            for task in tasks:
                if (task.id not in completed_tasks and 
                    task.id not in running_tasks and
                    dependency_graph[task.id].issubset(completed_tasks)):
                    ready_tasks.append(task)
            
            # Sort by priority
            ready_tasks.sort(key=lambda t: t.priority.value, reverse=True)
            
            # Start new tasks up to parallel limit
            while ready_tasks and len(running_tasks) < max_parallel:
                task = ready_tasks.pop(0)
                future = self._execute_task_async(task)
                running_tasks[task.id] = future
                task.status = TaskStatus.RUNNING
                task.start_time = datetime.now()
                logger.info(f"Started task: {task.id}")
            
            # Check completed tasks
            completed_futures = []
            for task_id, future in running_tasks.items():
                if future.done():
                    completed_futures.append(task_id)
                    try:
                        result = future.result()
                        results[task_id] = result
                        task_map[task_id].status = TaskStatus.COMPLETED
                        task_map[task_id].result = result
                        completed_tasks.add(task_id)
                        logger.info(f"Task completed: {task_id}")
                    except Exception as e:
                        task_map[task_id].status = TaskStatus.FAILED
                        task_map[task_id].error = str(e)
                        logger.error(f"Task failed: {task_id}, Error: {e}")
                        
                        # Handle retry logic
                        if task_map[task_id].retry_count > 0:
                            task_map[task_id].retry_count -= 1
                            task_map[task_id].status = TaskStatus.RETRYING
                            # Re-add to ready tasks for retry
                            ready_tasks.insert(0, task_map[task_id])
                        else:
                            # Task permanently failed
                            raise Exception(f"Task {task_id} failed permanently: {e}")
                    
                    task_map[task_id].end_time = datetime.now()
                    task_map[task_id].execution_time = (
                        task_map[task_id].end_time - task_map[task_id].start_time
                    ).total_seconds()
            
            # Remove completed futures
            for task_id in completed_futures:
                del running_tasks[task_id]
            
            # Small delay to prevent busy waiting
            if not completed_futures:
                await asyncio.sleep(0.1)
        
        return results
    
    def _execute_task_async(self, task: WorkflowTask) -> Future:
        """Execute a single task asynchronously"""
        if task.agent_type not in self.agent_processors:
            raise ValueError(f"No processor registered for agent type: {task.agent_type}")
        
        processor = self.agent_processors[task.agent_type]
        
        # Submit task to thread pool
        future = self.executor.submit(self._execute_task_sync, task, processor)
        return future
    
    def _execute_task_sync(self, task: WorkflowTask, processor: Callable) -> Dict[str, Any]:
        """Execute a task synchronously"""
        try:
            logger.info(f"Executing task: {task.id} with agent: {task.agent_type}")
            result = processor(task.payload)
            
            return {
                'task_id': task.id,
                'status': 'success',
                'result': result,
                'agent_type': task.agent_type,
                'execution_time': time.time()
            }
        except Exception as e:
            logger.error(f"Task execution error: {task.id}, Error: {e}")
            raise e
    
    def _update_performance_metrics(self, workflow: WorkflowDefinition, results: Dict[str, Any]):
        """Update performance metrics"""
        # Calculate execution times
        total_time = sum(task.execution_time for task in workflow.tasks if task.execution_time > 0)
        self.performance_metrics['execution_times'].append(total_time)
        
        # Calculate success rate
        successful_tasks = len([r for r in results.values() if r.get('status') == 'success'])
        success_rate = successful_tasks / len(workflow.tasks) if workflow.tasks else 0
        self.performance_metrics['success_rates'].append(success_rate)
        
        # Calculate parallel efficiency (theoretical vs actual time)
        sequential_time = sum(task.execution_time for task in workflow.tasks)
        parallel_efficiency = sequential_time / total_time if total_time > 0 else 0
        self.performance_metrics['parallel_efficiency'].append(parallel_efficiency)
    
    def _get_workflow_metrics(self, workflow_id: str) -> Dict[str, Any]:
        """Get performance metrics for a workflow"""
        if not self.performance_metrics['execution_times']:
            return {'status': 'no_data'}
        
        return {
            'average_execution_time': sum(self.performance_metrics['execution_times']) / len(self.performance_metrics['execution_times']),
            'average_success_rate': sum(self.performance_metrics['success_rates']) / len(self.performance_metrics['success_rates']),
            'average_parallel_efficiency': sum(self.performance_metrics['parallel_efficiency']) / len(self.performance_metrics['parallel_efficiency']),
            'total_workflows_executed': len(self.performance_metrics['execution_times'])
        }
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get current status of a workflow"""
        if workflow_id not in self.workflow_status:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        return self.workflow_status[workflow_id]
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow"""
        if workflow_id not in self.active_workflows:
            return False
        
        status = self.workflow_status[workflow_id]
        if status['status'] == 'running':
            status['status'] = 'cancelled'
            status['end_time'] = datetime.now()
            logger.info(f"Cancelled workflow: {workflow_id}")
            return True
        
        return False
    
    def get_all_workflows(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all workflows"""
        return self.workflow_status.copy()
    
    def cleanup_completed_workflows(self, older_than_hours: int = 24):
        """Clean up old completed workflows"""
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        workflows_to_remove = []
        
        for workflow_id, status in self.workflow_status.items():
            if (status['status'] in ['completed', 'failed', 'cancelled'] and
                status.get('end_time') and 
                status['end_time'] < cutoff_time):
                workflows_to_remove.append(workflow_id)
        
        for workflow_id in workflows_to_remove:
            del self.active_workflows[workflow_id]
            del self.workflow_status[workflow_id]
            logger.info(f"Cleaned up old workflow: {workflow_id}")
        
        return len(workflows_to_remove)

# Global orchestrator instance
orchestrator = WorkflowOrchestrator()

# Convenience functions for workflow creation
def create_simple_workflow(name: str, tasks: List[Dict[str, Any]]) -> WorkflowDefinition:
    """Create a simple workflow from task definitions"""
    workflow_tasks = []
    
    for i, task_def in enumerate(tasks):
        task = WorkflowTask(
            id=task_def.get('id', f"task_{i}"),
            name=task_def.get('name', f"Task {i}"),
            agent_type=task_def['agent_type'],
            payload=task_def['payload'],
            priority=TaskPriority(task_def.get('priority', 2)),
            dependencies=task_def.get('dependencies', []),
            timeout=task_def.get('timeout', 30.0),
            retry_count=task_def.get('retry_count', 3)
        )
        workflow_tasks.append(task)
    
    return WorkflowDefinition(
        id=f"workflow_{int(time.time())}",
        name=name,
        description=f"Auto-generated workflow: {name}",
        tasks=workflow_tasks
    )

def create_analysis_workflow(message: str, include_recommendations: bool = True) -> WorkflowDefinition:
    """Create a comprehensive analysis workflow"""
    tasks = [
        {
            'id': 'chat_analysis',
            'name': 'Chat Analysis',
            'agent_type': 'chat',
            'payload': {
                'message': f'Analyze this request: {message}',
                'context': {'analysis_type': 'comprehensive'}
            },
            'priority': 3
        },
        {
            'id': 'system_analytics',
            'name': 'System Analytics',
            'agent_type': 'analytics',
            'payload': {
                'message': f'Provide system analytics for: {message}',
                'context': {'analysis_depth': 'detailed'}
            },
            'priority': 3
        },
        {
            'id': 'device_status',
            'name': 'Device Status Check',
            'agent_type': 'device',
            'payload': {
                'message': f'Check device status related to: {message}',
                'context': {'check_type': 'comprehensive'}
            },
            'priority': 2
        },
        {
            'id': 'operations_health',
            'name': 'Operations Health',
            'agent_type': 'operations',
            'payload': {
                'message': f'Check operations health for: {message}',
                'context': {'health_check': 'full'}
            },
            'priority': 2
        }
    ]
    
    if include_recommendations:
        tasks.append({
            'id': 'automation_recommendations',
            'name': 'Automation Recommendations', 
            'agent_type': 'automation',
            'payload': {
                'message': f'Suggest automations for: {message}',
                'context': {'recommendation_type': 'proactive'}
            },
            'dependencies': ['chat_analysis', 'system_analytics'],
            'priority': 1
        })
    
    return create_simple_workflow(f"Comprehensive Analysis: {message[:50]}...", tasks)

# Example usage and testing
if __name__ == "__main__":
    import asyncio
    
    async def test_orchestrator():
        """Test the workflow orchestrator"""
        print("Testing Workflow Orchestrator...")
        
        # Create a test workflow
        workflow = create_analysis_workflow("Test system performance and suggest improvements")
        workflow_id = orchestrator.create_workflow(workflow)
        
        print(f"Created workflow: {workflow_id}")
        
        # Execute the workflow
        result = await orchestrator.execute_workflow(workflow_id)
        
        print("Workflow execution result:")
        print(json.dumps(result, indent=2, default=str))
        
        # Get final status
        status = orchestrator.get_workflow_status(workflow_id)
        print("Final workflow status:")
        print(json.dumps(status, indent=2, default=str))
    
    # Run test
    asyncio.run(test_orchestrator())
