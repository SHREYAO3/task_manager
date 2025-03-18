// Task Manager frontend functionality

// Function to highlight the current task row when clicked
document.addEventListener('DOMContentLoaded', function() {
    const taskRows = document.querySelectorAll('tbody tr');
    
    taskRows.forEach(row => {
        row.addEventListener('click', function(e) {
            // Don't trigger when clicking buttons
            if (e.target.tagName === 'A' || e.target.tagName === 'BUTTON') {
                return;
            }
            
            // Remove highlight from other rows
            taskRows.forEach(r => r.classList.remove('selected'));
            
            // Add highlight to clicked row
            this.classList.add('selected');
        });
    });
    
    // Add task filtering functionality
    const priorityFilter = document.getElementById('priority-filter');
    
    if (priorityFilter) {
        priorityFilter.addEventListener('change', function() {
            const value = this.value;
            
            taskRows.forEach(row => {
                if (value === 'all') {
                    row.style.display = '';
                } else {
                    const priority = parseInt(row.className.match(/priority-(\d+)/)[1]);
                    
                    if (value === 'high' && priority >= 7) {
                        row.style.display = '';
                    } else if (value === 'medium' && priority >= 4 && priority <= 6) {
                        row.style.display = '';
                    } else if (value === 'low' && priority <= 3) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            });
        });
    }
    
    // Add confirmation for delete actions
    const deleteButtons = document.querySelectorAll('.danger');
    
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this task?')) {
                e.preventDefault();
            }
        });
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