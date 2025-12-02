from django.db import models
from django.contrib.auth.models import User 
from django.utils import timezone
# Create your models here.

class title(models.Model):
    name = models.CharField("Title", max_length=50)
    phonNo = models.CharField("Phone No", max_length=50)
    email = models.CharField("Email", max_length=50)
    address = models.CharField("Address", max_length=100)
    
    def __str__(self):
        return self.name

class schoollogo(models.Model):
    LogoText = models.TextField("Logo Text", max_length=50)
    LogoImage = models.FileField(upload_to="logo_images/")
    

class AboutSchool(models.Model):
    aboutus = models.CharField("About Us", max_length=50)
    mission = models.CharField("Mission", max_length=100)
    vision = models.CharField("Vision", max_length=100)
    aboutImage =  models.FileField(upload_to="aboutImage/")
    



class Department(models.Model):
    """Represents either a Department (University) or Class (Secondary School)"""
    LEVEL_CHOICES = [
        ('Secondary', 'Secondary School'),
        ('College', 'College'),
        ('Polytechnic', 'Polytechnic'),
        ('University', 'University'),
        ('Other', 'Other Institution'),
    ]

    institution_type = models.CharField(
        "Institution Type",
        max_length=20,
        choices=LEVEL_CHOICES,
        default='Secondary'
    )
    name = models.CharField("Department / Class Name", max_length=100, unique=True)
    description = models.TextField("Description", blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name = "Department / Class"
        verbose_name_plural = "Departments / Classes"

    def __str__(self):
        return f"{self.name} ({self.institution_type})"
    
    

class ClassGroup(models.Model):
    """
    Represents a sub-class or level connected to a Department.
    Example:
        - SS1, SS2, SS3 under Secondary School Department
        - 100L, 200L under University Department
    """
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="classes")
    name = models.CharField("Class / Level Name", max_length=100)
    description = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        unique_together = ('department', 'name')
        verbose_name = "Class / Level"
        verbose_name_plural = "Classes / Levels"

    def __str__(self):
        return f"{self.name} - {self.department.name}"




class Course(models.Model):
    """Represents either a Course (Tertiary) or Subject (Secondary)"""
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    # classgroup = models.ForeignKey(ClassGroup, verbose_name="Class / Level",  on_delete=models.CASCADE, related_name='courses')
    classgroup = models.ManyToManyField(
        ClassGroup, 
        verbose_name="Class / Level", 
        related_name='courses',
        blank=True
    )
    title = models.CharField("Course / Subject Title", max_length=100)
    code = models.CharField("Course / Subject Code", max_length=20, unique=False)
    description = models.TextField("Description", blank=True, null=True)
    credit_unit = models.PositiveIntegerField(
        default=1,
        help_text="Can represent credit units (University) or subject weight (Secondary)"
    )
    date_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['title']
        verbose_name = "Course / Subject"
        verbose_name_plural = "Courses / Subjects"

    def __str__(self):
        return f"{self.title} ({self.code})"


class Lecture(models.Model):
    CONTENT_TYPES = [
        ('VIDEO', 'Video'),
        ('PDF', 'PDF'),
        ('AUDIO', 'Audio'),
        ('LINK', 'External Link'),
    ]
    STATUS_CHOICES = [
        ('LIVE', 'Live'),
        ('DRAFT', 'Draft'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="lectures")
    content_type = models.CharField(max_length=10, choices=CONTENT_TYPES)
    file = models.FileField(upload_to="lectures/files/", blank=True, null=True)
    external_url = models.URLField(blank=True, null=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma separated tags")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="DRAFT")
    duration = models.PositiveIntegerField(blank=True, null=True, help_text="Duration in minutes")
    views = models.PositiveIntegerField(default=0)
    last_viewed = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def tag_list(self):
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def __str__(self):
        return f"{self.title} ({self.course})"
    

class LectureVote(models.Model):
    lecture = models.ForeignKey(Lecture, on_delete=models.CASCADE, related_name="votes")
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  # 1–5
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("lecture", "student")

class Teacher(models.Model):
    """Universal model for Teachers or Lecturers"""
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    full_name = models.CharField("Full Name", max_length=150)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male')
    department = models.ManyToManyField(
    Department, 
        blank=True, 
        related_name='teachers', 
        verbose_name="Departments"
    )
    courses = models.ManyToManyField(
        Course, 
        related_name='teachers', 
        blank=True, 
        verbose_name="Courses / Subjects"
    )
    class_groups = models.ManyToManyField(
        'ClassGroup',
        blank=True,
        related_name='teachers',
        verbose_name="Classes / Levels"  # human-readable name
    )
    qualification = models.CharField("Qualification", max_length=100, blank=True, null=True)
    profile_picture = models.ImageField(upload_to='teacher_profiles/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    date_joined = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = "Teacher / Lecturer"
        verbose_name_plural = "Teachers / Lecturers"

    def __str__(self):
        return self.full_name



class Student(models.Model):
    """Universal model for students in both secondary and higher institutions"""
    
    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name='student_profile'
    )
    full_name = models.CharField("Full Name", max_length=150)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='Male')
    department = models.ForeignKey(
        Department, on_delete=models.SET_NULL, null=True, related_name='students'
    )
    courses = models.ManyToManyField(
        Course, related_name='students', blank=True
    )

    admission_number = models.CharField(
        "Admission / Matric No.", max_length=50, unique=True
    )
    level_or_class = models.ForeignKey(ClassGroup, on_delete=models.CASCADE, verbose_name="Class / Level ")
    
    guardian_name = models.CharField(
        "Parent / Guardian Name", max_length=100, blank=True, null=True
    )
    guardian_phone = models.CharField(
        "Parent / Guardian Phone", max_length=20, blank=True, null=True
    )
    email = models.EmailField(blank=True, null=True)
    profile_picture = models.ImageField(
        upload_to='student_profiles/', blank=True, null=True
    )
    date_joined = models.DateField(auto_now_add=True)

    class Meta:
        ordering = ['full_name']
        verbose_name = "Student / Learner"
        verbose_name_plural = "Students / Learners"

    def __str__(self):
        return f"{self.full_name} ({self.admission_number})"
    



class Exam(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    class_groups = models.ForeignKey(ClassGroup, on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_created = models.DateTimeField(auto_now_add=True)
    

    def __str__(self):
        return f"{self.course.title} ({self.class_groups.name})"


class Question(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)
    correct_answer = models.CharField(max_length=1, choices=[
        ('A', 'Option A'),
        ('B', 'Option B'),
        ('C', 'Option C'),
        ('D', 'Option D')
    ])
    term = models.CharField("Term / Semester", max_length=50, choices=[
        ('First Term', 'First Term'),
        ('Second Term', 'Second Term'),
        ('Third Term', 'Third Term'),
        ('Fourth Term', 'Fourth Term'),
        ('First Semester', 'First Semester'),
        ('Second Semester', 'Second Semester'),
        ('Third Semester', 'Third Semester'),
    ])


    def __str__(self):
        return self.question_text[:50]

# class Question(models.Model):
#     exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='questions')
#     question_text = models.TextField()
#     option_a = models.CharField(max_length=255)
#     option_b = models.CharField(max_length=255)
#     option_c = models.CharField(max_length=255)
#     option_d = models.CharField(max_length=255)
#     correct_answer = models.CharField(max_length=1, choices=[
#         ('A', 'Option A'),
#         ('B', 'Option B'),
#         ('C', 'Option C'),
#         ('D', 'Option D')
#     ])

#     def __str__(self):
#         return self.question_text[:50]


class ExamSchedule(models.Model):
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    class_level = models.ForeignKey(ClassGroup, on_delete=models.CASCADE)
    course_name = models.ForeignKey(Course, on_delete=models.CASCADE)
    scheduled_date = models.DateField()
    start_time = models.TimeField()
    duration_minutes = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    term = models.CharField("Term / Semester", max_length=50, choices=[
        ('First Term', 'First Term'),
        ('Second Term', 'Second Term'),
        ('Third Term', 'Third Term'),
        ('Fourth Term', 'Fourth Term'),
        ('First Semester', 'First Semester'),
        ('Second Semester', 'Second Semester'),
        ('Third Semester', 'Third Semester'),
    ])
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.exam.title} - {self.department.name} ({self.class_level.name})"
    
    
    @property
    def computed_status(self):
        today = timezone.localdate()
        now = timezone.localtime().time()

        if self.scheduled_date == today and self.start_time <= now:
            return "ongoing"
        elif self.scheduled_date > today or (self.scheduled_date == today and self.start_time > now):
            return "upcoming"
        else:
            return "completed"

    
    

class MarkedExam(models.Model):
    exam = models.ForeignKey('Exam', on_delete=models.CASCADE, related_name='marked_exams')
    student = models.ForeignKey('Student', on_delete=models.CASCADE, related_name='marked_exams')
    department = models.ForeignKey('Department', on_delete=models.SET_NULL, null=True)
    course = models.ForeignKey('Course', on_delete=models.SET_NULL, null=True)

    exam_number = models.CharField(max_length=50)
    username = models.CharField(max_length=150)
    full_name = models.CharField(max_length=150)
    total_score = models.PositiveIntegerField()
    total_questions = models.PositiveIntegerField()
    percentage = models.DecimalField(max_digits=5, decimal_places=2)

    date_taken = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.full_name} - {self.exam.title} ({self.total_score}/{self.total_questions})"
    
    class Meta:
        unique_together = ('exam', 'student')


class TestScore(models.Model):
    TEST_TYPE_CHOICES = [
        ('1st Test', '1st Test'),
        ('2nd Test', '2nd Test'),
        ('3rd Test', '3rd Test'),
    ]

    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    # class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE)
    class_group = models.CharField(max_length=20)
    total_questions = models.PositiveIntegerField()
    total_score = models.PositiveIntegerField()
    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES)
    date_added = models.DateTimeField(auto_now_add=True)
    percentage = models.FloatField(blank=True, null=True)


    def __str__(self):
        return f"{self.student.full_name} - {self.course.title} ({self.test_type})"

    @property
    def percentage(self):
        if self.total_questions:
            return round((self.total_score / self.total_questions) * 100, 2)
        return 0
    


class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"
    
    

class SliderImage(models.Model):
    title = models.CharField(max_length=150)
    image = models.ImageField(upload_to='slider_images/')
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']  # Latest images first

    def __str__(self):
        return self.title
    

class ResultAccessCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    students = models.ManyToManyField('Student', related_name='access_codes')
    # schedule_result_time = models.DateTimeField(null=True, blank=True)  # ✅ This field must exist

    def __str__(self):
        return self.code
    
class AgregatedPercentahe(models.Model):
    scorePercent = models.FloatField(
        unique=True,
        help_text="Enter the percentage multiplier for calculating exam scores (e.g. 100 for 100%)."
    )

    class Meta:
        verbose_name = 'Agregate Percentage'
        verbose_name = 'Agregate Percentage'
    
    
    def __str__(self):
        return f"{self.scorePercent}%"
    
    
