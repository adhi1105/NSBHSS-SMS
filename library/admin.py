from django.contrib import admin
from .models import Category, Book, BorrowRecord

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'shelf_location', 'available_copies', 'total_copies')
    list_filter = ('category',)
    search_fields = ('title', 'author', 'isbn')
    # Make it easy to adjust inventory directly from the list view
    list_editable = ('shelf_location', 'available_copies', 'total_copies')

@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    # Uses your custom property 'borrower_name' in the list view!
    list_display = ('book', 'borrower_name', 'status', 'issue_date', 'due_date', 'current_fine')
    list_filter = ('status', 'issue_date')
    search_fields = ('book__title', 'student__user__first_name', 'staff__user__first_name')
    
    # Use raw_id_fields so the dropdown doesn't crash when you have thousands of students
    raw_id_fields = ('book', 'student', 'staff')
    
    # Visual cues for status
    def get_status_color(self, obj):
        if obj.status == 'Returned': return 'green'
        if obj.status == 'Overdue': return 'red'
        return 'orange'