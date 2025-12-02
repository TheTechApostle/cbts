from django.contrib import admin
from .models import *
from django.utils.html import format_html
import csv
from django.http import HttpResponse
# Register your models here.
@admin.register(title)
class TitleAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')       # Columns to display in admin list view
    search_fields = ('name',)           # Enables search by name
    list_per_page = 20      
    

@admin.register(schoollogo)
class SchoolLogoAdmin(admin.ModelAdmin):
    list_display = ('LogoText', 'LogoText')       # Columns to display in admin list view
    search_fields = ('LogoText',)           # Enables search by name
    list_per_page = 20  
    
@admin.register(AboutSchool)
class AboutSchoolAdmin(admin.ModelAdmin):
    list_display = ('id', 'aboutus', 'mission', 'vision', 'preview_image')
    search_fields = ('aboutus', 'mission', 'vision')
    list_per_page = 10

    # To display a small image preview in the admin list
    def preview_image(self, obj):
        if obj.aboutImage:
            return f'<img src="{obj.aboutImage.url}" width="70" height="50" style="border-radius:5px;"/>'
        return "-"
    preview_image.allow_tags = True
    preview_image.short_description = "Image Preview"
    
    
@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'institution_type', 'description', 'date_created')
    list_filter = ('institution_type',)
    search_fields = ('name', 'institution_type')
    list_per_page = 20

class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1  # Show one empty form by default
    fields = ('question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer')
    show_change_link = True

@admin.register(Exam)
class ExamAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'course', 'created_by', 'date_created')
    search_fields = ('title', 'course__title', 'created_by__username')
    list_filter = ('course', 'date_created')
    inlines = [QuestionInline]

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'code', 'department', 'credit_unit', 'date_created')
    list_filter = ('department__institution_type',)
    search_fields = ('title', 'code', 'department__name')
    list_per_page = 20
    
@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'get_classes', 'get_courses','get_departments', 'email', 'phone', 'date_joined')
    list_filter = ('department__institution_type', 'gender')
    search_fields = ('full_name', 'email', 'department__name', 'class_groups__name')
    filter_horizontal = ('courses', 'department', 'class_groups')

    def get_departments(self, obj):
        return ", ".join([dept.name for dept in obj.department.all()])
    get_departments.short_description = "Departments"

    def get_classes(self, obj):
        return ", ".join([cls.name for cls in obj.class_groups.all()])
    get_classes.short_description = "Classes / Levels"
    
    def get_courses(self, obj):
        courses = obj.courses.all()
        if courses.exists():
            return ", ".join([course.title for course in courses])
        return "No course assigned"
    get_courses.short_description = "Courses"
    
    
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'admission_number', 'get_department', 'email', 'date_joined')
    list_filter = ('department__institution_type', 'gender')
    search_fields = ('full_name', 'admission_number', 'department__name', 'level_or_class__name')
    filter_horizontal = ('courses',)

    # Custom display for related fields
    def get_full_name(self, obj):
        return obj.full_name or obj.user.get_full_name()
    get_full_name.short_description = 'Full Name'

    def get_department(self, obj):
        return obj.department.name if obj.department else "-"
    get_department.short_description = 'Department'
    
    def get_classgroup(self, obj):
        """Return the class or level name."""
        return obj.level_or_class.name if obj.level_or_class else "-"
    get_classgroup.short_description = 'Class / Level'


@admin.register(ClassGroup)
class ClassGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'department', 'description', 'date_created')
    list_filter = ('department__institution_type', 'department')
    search_fields = ('name', 'department__name')
    ordering = ('department', 'name')
    readonly_fields = ('date_created',)
    
# Question Admin (optional standalone view)
@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('exam', 'question_text', 'correct_answer', 'term')
    search_fields = ('exam__title', 'question_text')
    list_filter = ('exam',)
    
    
    
@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = (
        'exam', 
        'department', 
        'class_level', 
        'course_name', 
        'scheduled_date', 
        'start_time', 
        'duration_minutes', 
        'total_questions', 
        'term', 
        'created_by', 
        'created_on'
    )
    list_filter = ('department', 'class_level', 'term', 'scheduled_date')
    search_fields = ('exam__title', 'course_name__title', 'department__name')
    ordering = ('scheduled_date', 'start_time')
    readonly_fields = ('created_on', 'created_by')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # Set the creator on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        





@admin.register(MarkedExam)
class MarkedExamAdmin(admin.ModelAdmin):
    list_display = (
        "student",
        "exam",
        "course",
        "department",
        "total_score",
        "total_questions",
        "percentage",
        "date_taken",
    )
    list_filter = ("department", "course", "exam", "date_taken")
    search_fields = (
        "student__full_name",
        "exam__title",
        "course__title",
        "exam_number",
        "username",
    )
    readonly_fields = (
        "exam",
        "student",
        "department",
        "course",
        "exam_number",
        "username",
        "full_name",
        "total_score",
        "total_questions",
        "percentage",
        "date_taken",
    )
    ordering = ("-date_taken",)
    actions = ["export_to_csv"]  # ✅ add the export button

    # --------------------------------------
    # Custom Action: Export selected results to CSV
    # --------------------------------------
    def export_to_csv(self, request, queryset):
        """Export selected MarkedExam records to a CSV file."""
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="marked_exams.csv"'

        writer = csv.writer(response)
        writer.writerow([
            "Exam Title",
            "Course",
            "Department",
            "Student Name",
            "Username",
            "Exam Number",
            "Total Score",
            "Total Questions",
            "Percentage",
            "Date Taken",
        ])

        for exam in queryset:
            writer.writerow([
                exam.exam.title,
                exam.course.title if exam.course else "",
                exam.department.name if exam.department else "",
                exam.full_name,
                exam.username,
                exam.exam_number,
                exam.total_score,
                exam.total_questions,
                exam.percentage,
                exam.date_taken.strftime("%Y-%m-%d %H:%M"),
            ])

        return response

    export_to_csv.short_description = "Export selected Marked Exams to CSV"



@admin.register(TestScore)
class TestScoreAdmin(admin.ModelAdmin):
    list_display = ('id', 'student', 'course', 'department', 'class_group', 'total_score', 'total_questions', 'test_type', 'date_added')
    list_filter = ('course', 'department', 'class_group', 'test_type')
    search_fields = ('student__full_name', 'course__title')
    readonly_fields = ('percentage',)
    
    @admin.display(description='Percentage')
    def show_percentage(self, obj):
        return f"{obj.percentage}%"


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'subject', 'created_at')  # Columns to show in admin list view
    list_filter = ('created_at',)  # Filter by date
    search_fields = ('name', 'email', 'subject', 'message')  # Enable search bar
    readonly_fields = ('name', 'email', 'subject', 'message', 'created_at')  # Make fields read-only (optional)
    ordering = ('-created_at',)  # Latest first
    
    

@admin.register(SliderImage)
class SliderImageAdmin(admin.ModelAdmin):
    list_display = ('title', 'image_preview', 'created_at')
    readonly_fields = ('image_preview',)
    search_fields = ('title', 'description')
    ordering = ('-created_at',)

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="60" style="object-fit: cover;" />', obj.image.url)
        return "(No Image)"
    image_preview.short_description = 'Preview'




@admin.register(AgregatedPercentahe)
class AgregatedPercentaheAdmin(admin.ModelAdmin):
    list_display = ('scorePercent',)
    

    
@admin.register(ResultAccessCode)
class ResultAccessCodeAdmin(admin.ModelAdmin):
    list_display = ('code',)
    search_fields = ('code',)
    filter_horizontal = ('students',)  # ✅ Better for selecting multiple students
    

    def get_students(self, obj):
        # Show up to 3 student names
        names = obj.students.all().values_list('full_name', flat=True)[:3]
        return ', '.join(names) if names else "No students"
    get_students.short_description = "Assigned Students"