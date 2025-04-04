// Task Manager frontend functionality
document.addEventListener('DOMContentLoaded', function() {
    // Category filter functionality
    const categoryFilter = document.getElementById('category-filter');
    const sortOptions = document.getElementById('sort-options');
    const taskGrid = document.querySelector('.task-grid');
    const statCards = document.querySelectorAll('.stat-card');


    if (categoryFilter && sortOptions) {
        // Function to update tasks based on filters
        function updateTasks(filterType = '') {
            const category = categoryFilter.value;
            const sortBy = sortOptions.value;
            const statusFilter = document.getElementById('status-filter');
            const status = statusFilter ? statusFilter.value : '';
           
            // Show loading state
            const activeTasksContainer = document.getElementById('activeTasksContainer');
            const completedTasksContainer = document.getElementById('completedTasksContainer');
            if (activeTasksContainer) activeTasksContainer.style.opacity = '0.6';
            if (completedTasksContainer) completedTasksContainer.style.opacity = '0.6';
           
            // Build the query URL - don't include status=all as it's the default
            let url = `/filter_tasks?category=${encodeURIComponent(category)}&sort=${encodeURIComponent(sortBy)}`;
            if (status && status !== 'all') {
                url += `&status=${encodeURIComponent(status)}`;
            }
            if (filterType) {
                url += `&filter_type=${encodeURIComponent(filterType)}`;
            }
           
            console.log('Fetching tasks with URL:', url); // For debugging
           
            // Fetch filtered and sorted tasks
            fetch(url)
                .then(response => {
                    if (!response.ok) {
                        throw new Error('Network response was not ok');
                    }
                    return response.json();
                })
                .then(tasks => {
                    // Clear current tasks
                    if (activeTasksContainer) activeTasksContainer.innerHTML = '';
                    if (completedTasksContainer) completedTasksContainer.innerHTML = '';
                   
                    if (tasks.length === 0) {
                        // Show empty state in active tasks container
                        if (activeTasksContainer) {
                            activeTasksContainer.innerHTML = `
                                <div class="empty-state" style="grid-column: 1 / -1;">
                                    <i class="fas fa-clipboard-list empty-icon"></i>
                                    <h3>No tasks found</h3>
                                    <p>Try adjusting your filters to see more tasks.</p>
                                </div>
                            `;
                        }
                    } else {
                        // Separate tasks into active and completed
                        const activeTasks = tasks.filter(task => task.status !== 'completed');
                        const completedTasks = tasks.filter(task => task.status === 'completed');
                       
                        // Render active tasks
                        if (activeTasksContainer) {
                            if (activeTasks.length === 0) {
                                activeTasksContainer.innerHTML = `
                                    <div class="empty-state" style="grid-column: 1 / -1;">
                                        <i class="fas fa-clipboard-list empty-icon"></i>
                                        <h3>No active tasks</h3>
                                        <p>All tasks are completed or try different filters.</p>
                                    </div>
                                `;
                            } else {
                                activeTasks.forEach(task => {
                                    const taskCard = createTaskCard(task);
                                    activeTasksContainer.appendChild(taskCard);
                                });
                            }
                        }
                       
                        // Render completed tasks
                        if (completedTasksContainer) {
                            if (completedTasks.length === 0) {
                                completedTasksContainer.innerHTML = `
                                    <div class="empty-state" style="grid-column: 1 / -1;">
                                        <i class="fas fa-clipboard-list empty-icon"></i>
                                        <h3>No completed tasks</h3>
                                        <p>Complete some tasks to see them here.</p>
                                    </div>
                                `;
                            } else {
                                completedTasks.forEach(task => {
                                    const taskCard = createTaskCard(task);
                                    completedTasksContainer.appendChild(taskCard);
                                });
                            }
                        }
                    }
                   
                    // Restore opacity
                    if (activeTasksContainer) activeTasksContainer.style.opacity = '1';
                    if (completedTasksContainer) completedTasksContainer.style.opacity = '1';
                })
                .catch(error => {
                    console.error('Error fetching tasks:', error);
                    if (activeTasksContainer) activeTasksContainer.style.opacity = '1';
                    if (completedTasksContainer) completedTasksContainer.style.opacity = '1';
                });
        }


        // Helper function to create task card HTML
        function createTaskCard(task) {
            const card = document.createElement('div');
            const isCompleted = task.status === 'completed';
            card.className = `task-card priority-${Math.round(task.priority)} status-${task.status || 'pending'} ${isCompleted ? 'task-completed' : ''}`;
            card.setAttribute('data-task-id', task.id);
           
            card.innerHTML = `
                <div class="task-card-header">
                    <div class="priority-badge">${task.priority.toFixed(1)}</div>
                    <div class="status-badge ${task.status || 'pending'}">${task.status || 'pending'}</div>
                </div>
                <div class="task-meta-info">
                    <div class="task-category-label">
                        <i class="fas fa-folder"></i> ${task.category}
                    </div>
                    <div class="task-type-label">
                        <i class="fas fa-tag"></i> ${task.type}
                    </div>
                </div>
                <div class="task-card-body">
                    <h3 class="task-title">${task.title}</h3>
                    <p class="task-description" title="${task.description}">${task.description}</p>
                   
                    <div class="task-metrics">
                        <div class="metric">
                            <i class="fas fa-calendar-alt"></i>
                            <span>${task.deadline_datetime.replace(' ', ' at ')}</span>
                        </div>
                        <div class="metric ${task.deadline_days <= 1 ? 'urgent' : task.deadline_days <= 3 ? 'warning' : ''}">
                            <i class="fas fa-hourglass-half"></i>
                            <span>${task.deadline_days} days left</span>
                        </div>
                        <div class="metric">
                            <i class="fas fa-clock"></i>
                            <span>${task.effort}h effort</span>
                        </div>
                        <div class="metric">
                            <i class="fas fa-exclamation-circle"></i>
                            <span>Urgency: ${task.urgency}</span>
                        </div>
                    </div>
                </div>
                <div class="task-card-actions">
                    <div class="task-status">
                        <select class="status-dropdown" onchange="updateTaskStatus('${task.id}', this.value)">
                            <option value="pending" ${!task.status || task.status === 'pending' ? 'selected' : ''}>Pending</option>
                            <option value="in-progress" ${task.status === 'in-progress' ? 'selected' : ''}>In Progress</option>
                            <option value="review" ${task.status === 'review' ? 'selected' : ''}>In Review</option>
                            <option value="completed" ${task.status === 'completed' ? 'selected' : ''}>Completed</option>
                        </select>
                    </div>
                    <div class="task-actions">
                        <a href="/view_task/${task.id}" class="btn btn-info btn-sm me-2" title="View Details">
                            <i class="fas fa-eye"></i>
                        </a>
                        ${!isCompleted ? `
                            <a href="/edit_task/${task.id}" class="btn btn-primary btn-sm me-2" title="Edit">
                                <i class="fas fa-edit"></i>
                            </a>
                        ` : ''}
                        <button onclick="deleteTask('${task.id}')" class="btn btn-danger btn-sm" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `;
           
            return card;
        }


        // Add event listeners for filters
        categoryFilter.addEventListener('change', () => updateTasks());
        sortOptions.addEventListener('change', () => updateTasks());
        const statusFilter = document.getElementById('status-filter');
        if (statusFilter) {
            statusFilter.addEventListener('change', () => updateTasks());
        }


        // Add event listeners for stat cards
        statCards.forEach(card => {
            card.addEventListener('click', function() {
                // Remove active class from all cards
                statCards.forEach(c => c.classList.remove('active'));
               
                // Add active class to clicked card
                this.classList.add('active');
               
                // Get the filter type from data attribute
                const filterType = this.dataset.filter;
               
                console.log('Stat card clicked:', filterType); // For debugging
               
                // Reset category filter
                if (categoryFilter) {
                    categoryFilter.value = '';
                }
               
                // Reset status filter
                if (statusFilter) {
                    statusFilter.value = '';
                }
               
                // Update tasks with filter
                updateTasks(filterType);
            });
        });
    }


    // Add confirmation for delete actions
    document.addEventListener('click', function(e) {
        if (e.target.closest('.btn-delete')) {
            if (!confirm('Are you sure you want to delete this task?')) {
                e.preventDefault();
            }
        }
    });


    // Function to calculate days left
    function calculateDaysLeft(deadlineDatetime) {
        const deadline = new Date(deadlineDatetime.replace(' ', 'T'));
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        deadline.setHours(0, 0, 0, 0);
       
        const diffTime = deadline - today;
        const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
        return Math.max(0, diffDays);
    }


    // Function to update days left for all tasks
    function updateDaysLeft() {
        const taskCards = document.querySelectorAll('.task-card');
        taskCards.forEach(card => {
            const deadlineSpan = card.querySelector('.metric:nth-child(1) span');
            const daysLeftSpan = card.querySelector('.metric:nth-child(2) span');
            const daysLeftMetric = card.querySelector('.metric:nth-child(2)');
           
            if (deadlineSpan && daysLeftSpan) {
                const deadlineDatetime = deadlineSpan.textContent.replace(' at ', ' ');
                const daysLeft = calculateDaysLeft(deadlineDatetime);
                daysLeftSpan.textContent = `${daysLeft} days left`;
               
                // Update urgency classes
                daysLeftMetric.className = `metric ${daysLeft <= 1 ? 'urgent' : daysLeft <= 3 ? 'warning' : ''}`;
            }
        });
    }


    // Update days left every minute
    setInterval(updateDaysLeft, 60000);


    // Initial update when page loads
    updateDaysLeft();
});


// Update styling for task rows based on priority
function updatePriorityStyles() {
    const rows = document.querySelectorAll('tbody tr');
   
    rows.forEach(row => {
        const priority = parseFloat(row.querySelector('.priority-indicator').textContent);
       
        // Remove existing priority classes
        for (let i = 1; i <= 10; i++) {
            row.classList.remove(`priority-${i}`);
        }
       
        // Add correct priority class
        row.classList.add(`priority-${Math.round(priority)}`);
    });
}


// Call this after any dynamic updates to task list
document.addEventListener('DOMContentLoaded', updatePriorityStyles);


function updateTaskStatus(taskId, status) {
    fetch(`/update_task_status/${taskId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ status: status })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.success) {
            // Update the tasks view with the latest data
            updateTasks();
        } else {
            // Show error message
            alert('Failed to update task status: ' + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while updating the task status');
    });
}


function renderTasks(tasks) {
    const taskListContainer = document.getElementById('taskListContainer');
   
    if (tasks.length === 0) {
        taskListContainer.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-clipboard-list empty-icon"></i>
                <h3>No tasks found with the selected filters</h3>
                <p>Try different filter options or <a href="{{ url_for('index') }}">view all tasks</a></p>
            </div>
        `;
        return;
    }
   
    let tasksHTML = '<div class="task-grid">';
   
    tasks.forEach(task => {
        const isCompleted = task.status === 'completed';
        tasksHTML += `
            <div class="task-card priority-${Math.floor(task.priority)} status-${task.status || 'pending'} ${isCompleted ? 'task-completed' : ''}" data-task-id="${task.id}">
                <div class="task-card-header">
                    <div class="priority-badge">${task.priority.toFixed(1)}</div>
                    <div class="status-badge ${task.status || 'pending'}">${task.status || 'pending'}</div>
                </div>
                <div class="task-meta-info">
                    <div class="task-category-label">
                        <i class="fas fa-folder"></i> ${task.category}
                    </div>
                    <div class="task-type-label">
                        <i class="fas fa-tag"></i> ${task.type}
                    </div>
                </div>
                <div class="task-card-body">
                    <h3 class="task-title">${task.title}</h3>
                    <p class="task-description" title="${task.description}">${task.description}</p>
                    <div class="task-metrics">
                        <div class="metric">
                            <i class="fas fa-calendar-alt"></i>
                            <span>${task.deadline_datetime.replace(' ', ' at ')}</span>
                        </div>
                        <div class="metric ${task.deadline_days <= 1 ? 'urgent' : task.deadline_days <= 3 ? 'warning' : ''}">
                            <i class="fas fa-hourglass-half"></i>
                            <span>${task.deadline_days} days left</span>
                        </div>
                        <div class="metric">
                            <i class="fas fa-clock"></i>
                            <span>${task.effort}h effort</span>
                        </div>
                        <div class="metric">
                            <i class="fas fa-exclamation-circle"></i>
                            <span>Urgency: ${task.urgency}</span>
                        </div>
                    </div>
                </div>
                <div class="task-card-actions">
                    <div class="task-status">
                        <select class="status-dropdown" onchange="updateTaskStatus('${task.id}', this.value)">
                            <option value="pending" ${task.status === 'pending' || !task.status ? 'selected' : ''}>Pending</option>
                            <option value="in-progress" ${task.status === 'in-progress' ? 'selected' : ''}>In Progress</option>
                            <option value="review" ${task.status === 'review' ? 'selected' : ''}>In Review</option>
                            <option value="completed" ${task.status === 'completed' ? 'selected' : ''}>Completed</option>
                        </select>
                    </div>
                    <div class="task-actions">
                        <a href="/view_task/${task.id}" class="btn btn-info btn-sm me-2" title="View Details">
                            <i class="fas fa-eye"></i>
                        </a>
                        ${!isCompleted ? `
                            <a href="/edit_task/${task.id}" class="btn btn-primary btn-sm me-2" title="Edit">
                                <i class="fas fa-edit"></i>
                            </a>
                        ` : ''}
                        <button onclick="deleteTask('${task.id}')" class="btn btn-danger btn-sm" title="Delete">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
    });
   
    tasksHTML += '</div>';
    taskListContainer.innerHTML = tasksHTML;
}