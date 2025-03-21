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
           
            // Show loading state
            taskGrid.style.opacity = '0.6';
           
            // Build the query URL
            let url = `/filter_tasks?category=${encodeURIComponent(category)}&sort=${encodeURIComponent(sortBy)}`;
            if (filterType) {
                url += `&filter_type=${encodeURIComponent(filterType)}`;
            }
           
            // Fetch filtered and sorted tasks
            fetch(url)
                .then(response => response.json())
                .then(tasks => {
                    taskGrid.innerHTML = ''; // Clear current tasks
                   
                    if (tasks.length === 0) {
                        // Show empty state
                        taskGrid.innerHTML = `
                            <div class="empty-state" style="grid-column: 1 / -1;">
                                <i class="fas fa-clipboard-list empty-icon"></i>
                                <h3>No tasks found</h3>
                                <p>Try adjusting your filters to see more tasks.</p>
                            </div>
                        `;
                    } else {
                        tasks.forEach(task => {
                            // Create task card HTML
                            const taskCard = createTaskCard(task);
                            taskGrid.appendChild(taskCard);
                        });
                    }
                   
                    taskGrid.style.opacity = '1';
                })
                .catch(error => {
                    console.error('Error fetching tasks:', error);
                    taskGrid.style.opacity = '1';
                });
        }


        // Helper function to create task card HTML
        function createTaskCard(task) {
            const card = document.createElement('div');
            card.className = `task-card priority-${Math.round(task.priority)}`;
           
            card.innerHTML = `
                <div class="task-card-header">
                    <div class="priority-badge">${task.priority.toFixed(1)}</div>
                    <div class="task-meta">
                        <span class="task-category">${task.category}</span>
                        <span class="task-type">${task.type}</span>
                    </div>
                </div>
                <div class="task-card-body">
                    <h3 class="task-title">${task.title}</h3>
                    <p class="task-description">${task.description}</p>
                   
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
                            <span>Urgency: ${task.urgency}/10</span>
                        </div>
                    </div>
                </div>
                <div class="task-card-actions">
                    <a href="/complete_task/${task.id}" class="btn btn-complete">
                        <i class="fas fa-check"></i> Complete
                    </a>
                    <a href="/delete_task/${task.id}" class="btn btn-delete" onclick="return confirm('Are you sure you want to delete this task?')">
                        <i class="fas fa-trash"></i> Delete
                    </a>
                </div>
            `;
           
            return card;
        }


        // Add event listeners for filters
        categoryFilter.addEventListener('change', () => updateTasks());
        sortOptions.addEventListener('change', () => updateTasks());


        // Add event listeners for stat cards
        statCards.forEach(card => {
            card.addEventListener('click', function() {
                // Remove active class from all cards
                statCards.forEach(c => c.classList.remove('active'));
               
                // Add active class to clicked card
                this.classList.add('active');
               
                // Get the filter type from data attribute
                const filterType = this.dataset.filter;
               
                // Reset category filter
                categoryFilter.value = '';
               
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