import os

# --- 1. Define the HTML Content for Teacher Selection ---
teacher_select_html = """{% extends 'base.html' %}

{% block content %}
<div class="d-flex align-items-center justify-content-center min-vh-70 py-5">
    <div class="card border-0 shadow-lg rounded-4 overflow-hidden" style="max-width: 500px; width: 100%;">
        <div class="card-header bg-primary text-white p-4 text-center">
            <h4 class="fw-bold m-0">Marks Entry</h4>
            <p class="small opacity-75 m-0">Select criteria to proceed</p>
        </div>
        <div class="card-body p-4">
            {% if messages %}
                {% for message in messages %}
                <div class="alert alert-{{ message.tags }} rounded-3 small mb-4">{{ message }}</div>
                {% endfor %}
            {% endif %}

            <div class="mb-3">
                <label class="form-label small fw-bold text-muted text-uppercase">Select Exam</label>
                <select id="exam_id" class="form-select form-select-lg bg-light border-0">
                    {% for e in exams %}
                    <option value="{{ e.id }}">{{ e.name }}</option>
                    {% empty %}
                    <option disabled selected>No Active Exams</option>
                    {% endfor %}
                </select>
            </div>

            <div class="mb-3">
                <label class="form-label small fw-bold text-muted text-uppercase">Select Class</label>
                <select id="class_id" class="form-select form-select-lg bg-light border-0">
                    {% for c in classes %}
                    <option value="{{ c.id }}">{{ c.name }}</option>
                    {% endfor %}
                </select>
            </div>

            <div class="mb-4">
                <label class="form-label small fw-bold text-muted text-uppercase">Select Subject</label>
                <select id="subject_id" class="form-select form-select-lg bg-light border-0">
                    {% for s in subjects %}
                    <option value="{{ s.id }}">{{ s.name }}</option>
                    {% endfor %}
                </select>
            </div>

            <button onclick="goToEntry()" class="btn btn-primary w-100 py-3 rounded-pill fw-bold shadow-sm">
                Proceed to Grading <i class="bi bi-arrow-right ms-2"></i>
            </button>
        </div>
    </div>
</div>

<script>
function goToEntry() {
    let exam = document.getElementById('exam_id').value;
    let cls = document.getElementById('class_id').value;
    let sub = document.getElementById('subject_id').value;
    
    if (!exam || !cls || !sub) {
        alert("Please select all fields.");
        return;
    }
    window.location.href = `/exam/marks/enter/${exam}/${cls}/${sub}/`;
}
</script>
{% endblock %}
"""

# --- 2. Define the HTML Content for Mark Entry ---
mark_entry_html = """{% extends 'base.html' %}
{% load custom_filters %}

{% block content %}
<div class="container py-4">
    <div class="d-flex justify-content-between align-items-end mb-4">
        <div>
            <a href="{% url 'exam:teacher_select' %}" class="text-decoration-none small text-muted mb-1 d-block">
                <i class="bi bi-arrow-left me-1"></i> Back to Selection
            </a>
            <h2 class="fw-bold text-dark m-0">{{ subject.name }}</h2>
            <div class="text-muted">{{ classroom.name }} • {{ exam.name }}</div>
        </div>
        <div>
            <div class="badge bg-warning-subtle text-warning border border-warning-subtle px-3 py-2 rounded-pill">
                <i class="bi bi-lock-fill me-1"></i> Auto-Save Disabled (Click Save)
            </div>
        </div>
    </div>

    <form method="post" class="card border-0 shadow-sm rounded-4 overflow-hidden">
        {% csrf_token %}
        <div class="table-responsive">
            <table class="table table-hover align-middle mb-0">
                <thead class="bg-light text-muted small text-uppercase">
                    <tr>
                        <th class="ps-4 py-3" style="width: 30%;">Student Name</th>
                        <th class="py-3" style="width: 20%;">Marks (Max 100)</th>
                        <th class="py-3">Teacher's Remarks</th>
                    </tr>
                </thead>
                <tbody>
                    {% for student in students %}
                    <tr>
                        <td class="ps-4">
                            <div class="fw-bold text-dark">{{ student.user.get_full_name }}</div>
                            <div class="small text-muted">{{ student.student_id }}</div>
                        </td>
                        <td>
                            <input type="number" step="0.01" max="100" min="0" 
                                   name="mark_{{ student.id }}" 
                                   class="form-control fw-bold text-center"
                                   placeholder="-"
                                   value="{{ existing_data|get_mark:student.id }}"
                                   style="max-width: 100px;">
                        </td>
                        <td class="pe-4">
                            <input type="text" 
                                   name="remark_{{ student.id }}" 
                                   class="form-control form-control-sm text-muted"
                                   placeholder="Add comment..."
                                   value="{{ existing_data|get_remark:student.id }}">
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        <div class="card-footer bg-white p-4 border-top">
            <div class="d-flex justify-content-end gap-3">
                <a href="{% url 'exam:teacher_select' %}" class="btn btn-light rounded-pill px-4">Cancel</a>
                <button type="submit" class="btn btn-success rounded-pill px-5 fw-bold shadow-sm">Save All Marks</button>
            </div>
        </div>
    </form>
</div>
{% endblock %}
"""

# --- 3. Define the Python Filter Content ---
filters_py = """from django import template
register = template.Library()

@register.filter
def get_mark(dictionary, key):
    data = dictionary.get(key)
    return data['mark'] if data else ''

@register.filter
def get_remark(dictionary, key):
    data = dictionary.get(key)
    return data['remark'] if data else ''
"""

# --- 4. Helper Function to Create Files ---
def create_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write(content)
    print(f"✅ Created: {path}")

# --- 5. EXECUTE CREATION ---
print("--- Auto-Creating Missing Files ---")

# Create Templates
create_file("templates/exam/teacher_select.html", teacher_select_html)
create_file("templates/exam/mark_entry.html", mark_entry_html)

# Create Template Tags (Filters)
create_file("exam/templatetags/__init__.py", "")
create_file("exam/templatetags/custom_filters.py", filters_py)

print("--- DONE! ---")
print("👉 Please restart your server now: python manage.py runserver")