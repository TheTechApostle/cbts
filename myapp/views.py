from django.shortcuts import render, redirect, get_object_or_404
from .models import *
import os
from .forms import *
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from .models import Lecture, Course
from django.contrib import messages
from django.db import IntegrityError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.db.models import Count, Avg
from django.contrib.auth.models import Group
from django.utils.text import slugify
from django.core.mail import send_mail
from django.conf import settings
import csv
from django.http import HttpResponse
from datetime import datetime
from django.utils import timezone
# Create your views here.

def MyHome(request):
    getTitle = title.objects.all().first()
    getLogo = schoollogo.objects.all().first()
    GetAboutSchool = AboutSchool.objects.all().first()
    GetAboutSchoolSec = AboutSchool.objects.all()[1] if AboutSchool.objects.count() > 1 else None
    QuestionCount = Question.objects.distinct().count()
    TeacherCount = Teacher.objects.distinct().count()
    CourseCount = Course.objects.distinct().count()
    SliderImagex = SliderImage.objects.all()
    StudentCount = Student.objects.distinct().count()

    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        subject = request.POST.get('subject')
        message = request.POST.get('message')

        if not all([name, email, subject, message]):
            return JsonResponse({'error': 'All fields are required.'}, status=400)

        # Save to database
        ContactMessage.objects.create(
            name=name,
            email=email,
            subject=subject,
            message=message
        )

        # Send email
        try:
            send_mail(
                subject=f"New Contact Message: {subject}",
                message=f"From: {name} <{email}>\n\nMessage:\n{message}",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.DEFAULT_FROM_EMAIL],
                fail_silently=False,
            )
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

        # If AJAX request
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': 'Your message has been sent successfully!'})

        # Fallback (non-AJAX)
        messages.success(request, "Your message has been sent successfully!")
        return redirect('MyHome')

    context = {
        'getTitle': getTitle,
        'getLogo': getLogo,
        'AboutSchool': GetAboutSchool,
        'GetAboutSchoolSec': GetAboutSchoolSec,
        'QuestionCount': QuestionCount,
        'TeacherCount': TeacherCount,
        'courseCount': CourseCount,
        'StudentCount': StudentCount,
        'slides':SliderImagex
    }
    return render(request, 'index.html', context)


def load_classgroups(request):
    department_id = request.GET.get('department_id')
    classgroups = ClassGroup.objects.filter(department_id=department_id).values('id', 'name')
    return JsonResponse(list(classgroups), safe=False)


def load_courses(request):
    department_id = request.GET.get('department_id')
    classgroup_id = request.GET.get('classgroup_id')
    courses = Course.objects.filter(department_id=department_id, classgroup_id=classgroup_id).values('id', 'title')
    return JsonResponse(list(courses), safe=False)


def register_student(request):
    # Fetch school details
    getTitle = title.objects.first()
    getLogo = schoollogo.objects.first()
    GetAboutSchool = AboutSchool.objects.first()

    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                user = form.save()  # ✅ The form handles both User + Student creation internally

                # ✅ Automatically add to "Student" group
                student_group, _ = Group.objects.get_or_create(name='Student')
                user.groups.add(student_group)

                messages.success(request, f"✅ Student '{user.get_full_name()}' registered successfully!")
                return redirect('SuccessPage')  # change to your real success page
            except IntegrityError as e:
                if 'admission_number' in str(e):
                    messages.error(request, "⚠️ This admission/matric number already exists.")
                else:
                    messages.error(request, f"⚠️ Database error: {str(e)}")
        else:
            # Collect all form errors
            error_messages = []
            for field, errors in form.errors.items():
                for error in errors:
                    error_messages.append(f"{field}: {error}")
            messages.error(request, "⚠️ Please fix these errors: " + "; ".join(error_messages))
    else:
        form = StudentRegistrationForm()

    context = {
        'form': form,
        'getTitle': getTitle,
        'getLogo': getLogo,
        'AboutSchool': GetAboutSchool,
    }
    return render(request, 'student_registration.html', context)


def lecture_list(request):
    lectures = Lecture.objects.all().order_by("-created_at")
    courses = Course.objects.all()

    # Metrics
    total_lectures = lectures.count()
    total_views = sum(l.views for l in lectures)
    new_this_week = lectures.filter(created_at__gte=timezone.now()-timezone.timedelta(days=7)).count()
    avg_completion = 75  # placeholder, compute from sessions if you track them

    # Breakdown for charts
    types_breakdown = {}
    for l in lectures:
        types_breakdown[l.content_type] = types_breakdown.get(l.content_type, 0) + 1

    views_series = [
        {"date": l.created_at.strftime("%Y-%m-%d"), "views": l.views}
        for l in lectures.order_by("created_at")[:10]
    ]

    context = {
        "lectures": lectures,
        "courses": courses,
        "total_lectures": total_lectures,
        "total_views": total_views,
        "new_this_week": new_this_week,
        "avg_completion": avg_completion,
        "types_breakdown_json": json.dumps(types_breakdown),
        "views_series_json": json.dumps(views_series),
        "top_tags": [],  # compute if needed
        "recent_activity": [],  # fill with logs if you track them
    }
    return render(request, "elearning/lecture_list.html", context)


def lecture_preview(request, pk):
    lecture = get_object_or_404(Lecture, pk=pk)

    # Increment views and update last_viewed
    lecture.views += 1
    lecture.last_viewed = timezone.now()
    lecture.save()

    return render(request, "elearning/lecture_preview.html", {"lecture": lecture})


def lecture_student_view(request, pk):
    lecture = get_object_or_404(Lecture, pk=pk)
    avg_rating = lecture.votes.aggregate(Avg("rating"))["rating__avg"]
    return render(request, "elearning/lecture_student_view.html", {
        "lecture": lecture,
        "avg_rating": round(avg_rating or 0, 1),
    })

@csrf_exempt
def lecture_vote(request, pk):
    if request.method == "POST":
        lecture = get_object_or_404(Lecture, pk=pk)
        rating = int(request.POST.get("rating"))
        vote, created = LectureVote.objects.update_or_create(
            lecture=lecture, student=request.user,
            defaults={"rating": rating}
        )
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Invalid request"}, status=400)

def lecture_upload(request):
    if request.method == "POST":
        title = request.POST.get("title")
        course_id = request.POST.get("course_id")
        course = get_object_or_404(Course, id=course_id)
        content_type = request.POST.get("content_type")
        description = request.POST.get("description")
        tags = request.POST.get("tags", "")
        status = request.POST.get("status", "DRAFT")
        duration = request.POST.get("duration")

        lecture = Lecture.objects.create(
            title=title,
            description=description,
            course=course,
            content_type=content_type,
            tags=tags,
            status=status,
            duration=duration or None,
        )
        if content_type != "LINK" and "file" in request.FILES:
            lecture.file = request.FILES["file"]
        elif content_type == "LINK":
            lecture.external_url = request.POST.get("external_url")
        lecture.save()
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def lecture_toggle_status(request):
    if request.method == "POST":
        lecture_id = request.POST.get("lecture_id")
        lecture = get_object_or_404(Lecture, id=lecture_id)
        lecture.status = "LIVE" if lecture.status == "DRAFT" else "DRAFT"
        lecture.save()
        return JsonResponse({"success": True, "status": lecture.status})
    return JsonResponse({"error": "Invalid request"}, status=400)


@csrf_exempt
def lecture_delete(request):
    if request.method == "POST":
        lecture_id = request.POST.get("lecture_id")
        lecture = get_object_or_404(Lecture, id=lecture_id)
        lecture.delete()
        return JsonResponse({"success": True})
    return JsonResponse({"error": "Invalid request"}, status=400)


def export_lectures_csv(request):
    lectures = Lecture.objects.all()
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = 'attachment; filename="lectures.csv"'
    writer = csv.writer(response)
    writer.writerow(["Title", "Course", "Type", "Views", "Status", "Created"])
    for l in lectures:
        writer.writerow([l.title, l.course.title, l.content_type, l.views, l.status, l.created_at])
    return response

def register_teacher(request):
    getTitle = title.objects.first()
    getLogo = schoollogo.objects.first()
    GetAboutSchool = AboutSchool.objects.first()

    if request.method == 'POST':
        form = TeacherRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            teacher = form.save()  # ✅ form already creates linked user
            educator_group, _ = Group.objects.get_or_create(name='Educator')
            teacher.user.groups.add(educator_group)

            messages.success(request, f"✅ {teacher.full_name} registered successfully and added to Educator group.")
            return redirect('teacher_list')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field.replace('_', ' ').capitalize()}: {error}")
    else:
        form = TeacherRegistrationForm()

    context = {
        'form': form,
        'getTitle': getTitle,
        'getLogo': getLogo,
        'AboutSchool': GetAboutSchool,
    }
    return render(request, 'teacher_form.html', context)


def teacher_list(request):
    getTitle = title.objects.first()
    getLogo = schoollogo.objects.first()
    GetAboutSchool = AboutSchool.objects.first()
    teachers= Teacher.objects.all().select_related('user')  # Efficiently fetch related user info
    context = {
        'teachers': teachers,
        'getTitle': getTitle,
        'getLogo': getLogo,
        'AboutSchool': GetAboutSchool,
    }
    return render(request, 'teacher_list.html',context)


def SuccessPage(request):
    getTitle = title.objects.all().first()
    getLogo = schoollogo.objects.all().first()
    GetAboutSchool = AboutSchool.objects.all().first()
    context = {
        'getTitle':getTitle,
        'getLogo':getLogo,
        'AboutSchool':GetAboutSchool
    }
    return render(request, 'success_page.html', context)


def LoginUser(request):
    getTitle = title.objects.all().first()
    getLogo = schoollogo.objects.all().first()
    GetAboutSchool = AboutSchool.objects.all().first()
    
    next_url = request.GET.get('next') or request.POST.get('next') or None
    
    if request.method == "POST":
        form = LoginForm(request=request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if user.groups.filter(name="Educator").exists():
                return redirect("Teacherdashboard")

            if user.groups.filter(name="Student").exists():
                return redirect("student_portal")

            if url_has_allowed_host_and_scheme(next_url, allowed_hosts={request.get_host()}):
                return redirect(next_url)
            return redirect("dashboard")
        else:
            messages.warning(request, 'Authentication Failed... Username or Password Error')
    else:
        form = LoginForm()
    context = {
        'getTitle':getTitle,
        'getLogo':getLogo,
        'AboutSchool':GetAboutSchool,
        'form': form, 'next': next_url or '',
    }
    return render(request, 'login.html', context)

# API_URL = "https://router.huggingface.co/hf-inference/models/valurank/MiniLM-L6-Keyword-Extraction/pipeline/sentence-similarity"
import requests
API_FOR_GEN = "https://api-inference.huggingface.co/models/facebook/bart-large-cnn"

HF_TOKEN = settings.HF_TOKEN_API
API_URL = "https://router.huggingface.co/valurank/MiniLM-L6-Keyword-Extraction/pipeline/sentence-similarity"


headers = {"Authorization": f"Bearer {HF_TOKEN}"}

# Quick test function
# def test_connection():
#     response = requests.post(API_URL, headers=headers, json={"inputs": "test"})
#     try:
#         print("Status:", response.status_code)
#         print("Response:", response.text)
#     except Exception as e:
#         print("Error:", e, response.text)

# # Run the test
# test_connection()

API_URL = "https://api-inference.huggingface.co/models/valurank/MiniLM-L6-Keyword-Extraction"
headers = {
    "Authorization": f"Bearer {HF_TOKEN}",
}



def query(payload):
    response = requests.post(API_FOR_GEN, headers=headers, json=payload)
    return response.json()

text = "I want to learn about algebra in mathematics."
output = query({"inputs": text})
print(output)


def hr_query(payload):
    """Call HuggingFace Inference API safely."""
    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print("HF API Error:", e)
        return None


@login_required(login_url='LoginUser')
def student_dashboard(request):

    video_id = None
    raw_query = request.GET.get("q")

    # Run keyphrase extraction if user enters a query
    hr_result = None
    query_text = None

    if raw_query:
        hr_result = hr_query({"inputs": raw_query})

        # HuggingFace returns [{"score":..., "word": "keyword"}, ...]
        if isinstance(hr_result, list) and len(hr_result) > 0:
            query_text = hr_result[0].get("word")  # use best keyword
        else:
            query_text = raw_query

        # YOUTUBE SEARCH
        api_key = settings.YOUTUBE_API_KEY
        url = "https://www.googleapis.com/youtube/v3/search"

        params = {
            "part": "snippet",
            "q": query_text,
            "type": "video",
            "maxResults": 1,
            "key": api_key,
        }

        yt_response = requests.get(url, params=params).json()
        if yt_response.get("items"):
            video_id = yt_response["items"][0]["id"]["videoId"]

    # -------- DB DATA -------- #
    getTitle = title.objects.all().first()
    getLogo = schoollogo.objects.all().first()
    GetAboutSchool = AboutSchool.objects.all().first()
    GetAboutSchoolSec = AboutSchool.objects.all()[1] if AboutSchool.objects.count() > 1 else None

    student = get_object_or_404(Student, user=request.user)

    courses = (
        student.courses
        .all()
        .prefetch_related("lectures", "lectures__votes")
    )

    total_lectures = sum(c.lectures.count() for c in courses)
    total_votes = sum(l.votes.count() for c in courses for l in c.lectures.all())

    # Compute completed lectures for the chart
    for c in courses:
    # If no completed lecture logic yet, assume 0 completed
        c.completed_lectures = getattr(c, "completed_lectures", 0)
        c.remaining_lectures = c.lectures.count() - c.completed_lectures

    return render(request, "elearning/student_dashboard.html", {
        "student": student,
        "getTitle": getTitle,
        "getLogo": getLogo,
        "GetAboutSchool": GetAboutSchool,
        "GetAboutSchoolSec": GetAboutSchoolSec,

        "courses": courses,
        "total_lectures": total_lectures,
        "total_votes": total_votes,

        # VIDEO
        "video_id": video_id,
        "query": query_text
    })
    
    
@login_required(login_url='LoginUser')
def course_detail(request, course_id):
    getTitle = title.objects.all().first()
    getLogo = schoollogo.objects.all().first()
    GetAboutSchool = AboutSchool.objects.all().first()
    GetAboutSchoolSec = AboutSchool.objects.all()[1] if AboutSchool.objects.count() > 1 else None
    course = get_object_or_404(Course, id=course_id)
    return render(request, "elearning/course_detail.html", {
        "course": course,
        'getTitle':getTitle,
        'getLogo':getLogo,
        'GetAboutSchoolSec':GetAboutSchoolSec,
        'GetAboutSchool':GetAboutSchool,
        "student": request.user.student_profile,  # if you have Student linked to User
    })

@login_required
def logout_user(request):
    """Logs out the current user and redirects to login page."""
    logout(request)
    messages.success(request, "👋 You have been logged out successfully.")
    return redirect('LoginUser')  # Change to your actual login URL name

def dashboard(request):
    return render(request, 'dashboard.html')

def Teacherdashboard(request):
    getTitle = title.objects.all().first()
    getLogo = schoollogo.objects.all().first()
    GetAboutSchool = AboutSchool.objects.all().first()
    context = {
        'getTitle':getTitle,
        'getLogo':getLogo,
        'AboutSchool':GetAboutSchool,        
    }
    return render(request, 'Teacherdashboard.html', context)


@login_required
def add_questions(request, exam_id=None):
    teacher = getattr(request.user, 'teacher_profile', None)
    if not teacher:
        messages.error(request, "You must be logged in as a teacher.")
        return redirect('Teacherdashboard')

    departments = teacher.department.all()
    classes = teacher.class_groups.all()
    courses = teacher.courses.all()
    exam = None

    # Editing existing exam
    if exam_id:
        exam = get_object_or_404(Exam, id=exam_id)
        if exam.created_by != request.user:
            messages.error(request, "You don’t have permission to edit this exam.")
            return redirect('Teacherdashboard')

    # Handle course selection (create or reuse exam)
    elif request.method == 'POST' and 'select_course' in request.POST:
        dept_id = request.POST.get('department')
        class_id = request.POST.get('classgroup')
        course_id = request.POST.get('course')

        if not (dept_id and class_id and course_id):
            messages.warning(request, "Please select department, class, and course.")
            return redirect('add_questions')

        department = get_object_or_404(Department, id=dept_id)
        classgroup = get_object_or_404(ClassGroup, id=class_id)
        course = get_object_or_404(Course, id=course_id)

        # ✅ Check if exam already exists for this teacher, class, and course
        existing_exam = Exam.objects.filter(
            course=course,
            class_groups=classgroup,
            created_by=request.user,
            title__icontains=classgroup.name  # Adjust this if titles are unique differently
        ).first()

        if existing_exam:
            messages.info(request, f"Exam for '{course.title}' ({classgroup.name}) already exists.")
            return redirect('add_questions', exam_id=existing_exam.id)
        else:
            # Create new exam
            exam = Exam.objects.create(
                course=course,
                class_groups=classgroup,
                title=f"{course.title} Exam ({classgroup.name})",
                created_by=request.user,
            )
            messages.success(request, f"Exam '{exam.title}' created successfully.")
            return redirect('add_questions', exam_id=exam.id)

    # Add questions to an existing exam
    if request.method == 'POST' and 'save_questions' in request.POST:
        exam_id = request.POST.get('exam_id')
        exam = get_object_or_404(Exam, id=exam_id)

        created_count = 0
        question_index = 1
        term = request.POST.get('term', '').strip().title()

        while True:
            q_text = request.POST.get(f'question_text_{question_index}')
            if not q_text:
                break

            option_a = request.POST.get(f'option_a_{question_index}', '').strip()
            option_b = request.POST.get(f'option_b_{question_index}', '').strip()
            option_c = request.POST.get(f'option_c_{question_index}', '').strip()
            option_d = request.POST.get(f'option_d_{question_index}', '').strip()
            correct = request.POST.get(f'correct_answer_{question_index}', '').strip().upper()

            if q_text.strip() and correct in ['A', 'B', 'C', 'D']:
                Question.objects.create(
                    exam=exam,
                    question_text=q_text.strip(),
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_answer=correct,
                    term=term
                )
                created_count += 1

            question_index += 1

        if created_count:
            messages.success(request, f"{created_count} question(s) added to '{exam.title}'.")
            return redirect('exam_detail', exam_id=exam.id)
        else:
            messages.warning(request, "No valid questions were submitted.")

    context = {
        'exam': exam,
        'departments': departments,
        'classes': classes,
        'courses': courses,
        'teacher': teacher,
        'form': QuestionForm(),
    }
    return render(request, 'add_questions.html', context)



# @login_required
# def add_questions(request, exam_id=None):
#     teacher = getattr(request.user, 'teacher_profile', None)
#     if not teacher:
#         messages.error(request, "You must be logged in as a teacher.")
#         return redirect('Teacherdashboard')

#     departments = teacher.department.all()
#     classes = teacher.class_groups.all()
#     courses = teacher.courses.all()
#     exam = None

#     # --- Editing existing exam ---
#     if exam_id:
#         exam = get_object_or_404(Exam, id=exam_id)
#         if exam.created_by != request.user:
#             messages.error(request, "You don’t have permission to edit this exam.")
#             return redirect('Teacherdashboard')

#     # --- Handle course selection (create or reuse exam) ---
#     elif request.method == 'POST' and 'select_course' in request.POST:
#         dept_id = request.POST.get('department')
#         class_id = request.POST.get('classgroup')
#         course_id = request.POST.get('course')

#         if not (dept_id and class_id and course_id):
#             messages.warning(request, "Please select department, class, and course.")
#             return redirect('add_questions')

#         department = get_object_or_404(Department, id=dept_id)
#         classgroup = get_object_or_404(ClassGroup, id=class_id)
#         course = get_object_or_404(Course, id=course_id)

#         # ✅ Check if exam already exists for this teacher, class, and course
#         existing_exam = Exam.objects.filter(
#             course=course,
#             created_by=request.user,
#             title__icontains=classgroup.name
#         ).first()

#         if existing_exam:
#             messages.info(request, f"Exam for '{course.title}' ({classgroup.name}) already exists.")
#             return redirect('add_questions_with_id', exam_id=existing_exam.id)
#         else:
#             # ✅ Create new exam
#             exam = Exam.objects.create(
#                 course=course,
#                 title=f"{course.title} Exam ({classgroup.name})",
#                 created_by=request.user,
#             )
#             messages.success(request, f"Exam '{exam.title}' created successfully.")
#             return redirect('add_questions_with_id', exam_id=exam.id)

#     # --- Add questions to an existing exam ---
#     if request.method == 'POST' and 'save_questions' in request.POST:
#         exam_id = request.POST.get('exam_id')
#         exam = get_object_or_404(Exam, id=exam_id)

#         created_count = 0
#         question_index = 1
#         term = request.POST.get('term', '').strip().title()

#         while True:
#             q_text = request.POST.get(f'question_text_{question_index}')
#             if not q_text:
#                 break

#             option_a = request.POST.get(f'option_a_{question_index}', '').strip()
#             option_b = request.POST.get(f'option_b_{question_index}', '').strip()
#             option_c = request.POST.get(f'option_c_{question_index}', '').strip()
#             option_d = request.POST.get(f'option_d_{question_index}', '').strip()
#             correct = request.POST.get(f'correct_answer_{question_index}', '').strip().upper()

#             if q_text.strip() and correct in ['A', 'B', 'C', 'D']:
#                 Question.objects.create(
#                     exam=exam,
#                     question_text=q_text.strip(),
#                     option_a=option_a,
#                     option_b=option_b,
#                     option_c=option_c,
#                     option_d=option_d,
#                     correct_answer=correct,
#                     term=term
#                 )
#                 created_count += 1

#             question_index += 1

#         if created_count:
#             messages.success(request, f"{created_count} question(s) added to '{exam.title}'.")
#             return redirect('exam_detail', exam_id=exam.id)
#         else:
#             messages.warning(request, "No valid questions were submitted.")

#     context = {
#         'exam': exam,
#         'departments': departments,
#         'classes': classes,
#         'courses': courses,
#         'teacher': teacher,
#         'form': QuestionForm(),
#     }
#     return render(request, 'add_questions.html', context)




# def exam_detail(request, exam_id):
#     # Get the specific exam or return 404 if not found
#     exam = get_object_or_404(Exam, id=exam_id)
    
#     # Fetch all courses created by the same teacher
#     courses = Exam.objects.filter(created_by=exam.created_by).distinct()
    
#     # Fetch all questions for this exam
#     questions = Question.objects.filter(exam=exam).order_by('id')

#     context = {
#         'exam': exam,
#         'courses': courses,  # pass to template
#         'questions': questions,
#     }

#     return render(request, 'exam_details.html', context)


# @login_required
# def exam_detail(request, exam_id):
#     exam = get_object_or_404(Exam, id=exam_id)

#     teacher = request.user
#     exams = Exam.objects.filter(created_by=teacher).select_related('course').order_by('course__title')
#     questions = Question.objects.filter(exam=exam).order_by('id')

#     # Related info
#     # Related info
#     department = exam.course.department
#     course = exam.course
#     classgroup = exam.class_groups  # ✅ correct class group
#     all_classgroups = ClassGroup.objects.all().order_by('name')

#     # ✅ Fetch all exam schedules related to this exam
#     schedules = ExamSchedule.objects.filter(exam=exam).select_related(
#         'department', 'class_level', 'course_name'
#     ).order_by('-scheduled_date', '-start_time')  # Latest first

#     # ✅ If you still need a single schedule for modal or display
#     schedule = schedules.first() if schedules.exists() else None

#     # ✅ Get students registered for this course
#     students = Student.objects.filter(
#         courses=course,
#         level_or_class=classgroup
#     ).select_related('department').distinct()

#     context = {
#         'exam': exam,
#         'course': course,
#         'exams': exams,
#         'all_classgroups': all_classgroups, 
#         'questions': questions,
#         'department': department,
#         'classgroup': classgroup,
#         'students': students,
#         'schedules': schedules,  # ✅ all schedules
#         'schedule': schedule,    # ✅ first schedule (optional)
#     }

#     return render(request, 'exam_details.html', context)



@login_required
def exam_detail(request, exam_id):
    exam = get_object_or_404(
        Exam.objects.select_related('course__department').prefetch_related('questions'),
        id=exam_id
    )

    teacher = request.user

    # Fetch only this teacher's exams (for sidebar or listing)
    exams = (
        Exam.objects.filter(created_by=teacher)
        .select_related('course__department')
        .order_by('course__title')
    )

    import re
    for e in exams:
        class_name = e.class_groups.name.strip() if e.class_groups else ""
        raw_title = e.title.strip()

        # Remove any prefix like "SS1", "JSS2", "Year 1", etc.
        raw_title_clean = re.sub(r'^(SS|JSS|Grade|Year)\s*\d+\s*[A-Z]?\s*', '', raw_title, flags=re.IGNORECASE).strip()
        e.display_title = f"{class_name} {raw_title_clean}"
            
    course = exam.course
    department = course.department
    classgroup = exam.class_groups  # ✅ the assigned class
    print(classgroup)
    all_classgroups = ClassGroup.objects.all().order_by('name')

    # ✅ Get all exam schedules for this exam
    schedules = (
        ExamSchedule.objects.filter(exam=exam)
        .select_related('department', 'class_level', 'course_name')
        .order_by('-scheduled_date', '-start_time')
    )

    schedule = schedules.first() if schedules.exists() else None
    print(course)

    # ✅ Fetch all students registered for this course *and* class group
    students = (
        Student.objects.filter(courses=course, level_or_class=classgroup)
        .select_related('department', 'level_or_class')
        .distinct()
    )

    context = {
        'exam': exam,
        'course': course,
        'department': department,
        'classgroup': classgroup,
        'exams': exams,
        'questions': exam.questions.all(),
        'students': students,
        'all_classgroups': all_classgroups,
        'schedules': schedules,
        'schedule': schedule,
    }

    return render(request, 'exam_details.html', context)


@login_required
def MyStudent(request, classgroup_id, course_id):
    classgroup = get_object_or_404(ClassGroup, id=classgroup_id)
    course = get_object_or_404(Course, id=course_id)

    # ✅ Fetch students registered for this course AND in this class group
    students = (
        Student.objects.filter(
            level_or_class=classgroup,
            
        )
        .select_related('department', 'level_or_class')
        .distinct()
    )

    context = {
        'classgroup': classgroup,
        'course': course,
        'students': students,
    }

    return render(request, 'MyStudent.html', context)



@login_required
def publish_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.method == "POST":
        selected_ids = request.POST.getlist("class_groups")
        target_groups = ClassGroup.objects.filter(id__in=selected_ids)

        # Get all questions from the current exam
        questions = Question.objects.filter(exam=exam)

        published_to = []   # Keep track of new publications
        skipped = []        # Keep track of duplicates

        for group in target_groups:
            # ✅ Check if an exam already exists for this course and class group
            existing_exam = Exam.objects.filter(
                course=exam.course,
                class_groups=group,
                created_by=request.user
            ).first()

            if existing_exam:
                skipped.append(group.name)
                continue  # skip this one — it's already published

            # ✅ Create a new exam for this class group
            new_exam = Exam.objects.create(
                course=exam.course,
                class_groups=group,
                created_by=request.user,
                title=f"{exam.course.title} ({group.name} - {group.category})" if group.category else f"{exam.course.title} ({group.name})"

            )

            # ✅ Copy questions to the new exam
            Question.objects.bulk_create([
                Question(
                    exam=new_exam,
                    question_text=q.question_text,
                    option_a=q.option_a,
                    option_b=q.option_b,
                    option_c=q.option_c,
                    option_d=q.option_d,
                    correct_answer=q.correct_answer,
                    term = q.term
                ) for q in questions
            ])

            published_to.append(group.name)

        # ✅ Prepare feedback message
        message_parts = []
        if published_to:
            message_parts.append(f"Published to: {', '.join(published_to)}.")
        if skipped:
            message_parts.append(f"Skipped duplicates for: {', '.join(skipped)}.")

        message = " ".join(message_parts) or "No class groups selected."

        return JsonResponse({
            "success": True,
            "message": message
        })

    return JsonResponse({"error": "Invalid request."}, status=400)


@login_required
def edit_question(request):
    if request.method == "POST":
        qid = request.POST.get("question_id")
        question = get_object_or_404(Question, id=qid)
        question.question_text = request.POST.get("question_text")
        question.option_a = request.POST.get("option_a")
        question.option_b = request.POST.get("option_b")
        question.option_c = request.POST.get("option_c")
        question.option_d = request.POST.get("option_d")
        question.correct_answer = request.POST.get("correct_answer")
        question.term = request.POST.get("term")
        question.save()
        messages.success(request, "Question updated successfully!")
        return redirect('exam_detail', exam_id=question.exam.id)



def teacher_manage_course(request):
    teacher = request.user
    # Fetch all courses that have exams by this teacher
    courses = (
        Course.objects
        .filter(exam__created_by=teacher)
        .annotate(question_count=Count('exam__questions', distinct=True))  # ✅ Count questions per course
        .distinct()
        .prefetch_related('exam_set')
    )

    # ✅ Total count of all questions created by this teacher
    total_question_count = Question.objects.filter(exam__created_by=teacher).count()

    context = {
        'courses': courses,
        'total_question_count': total_question_count
    }
    return render(request, 'teacher_manage_course.html', context)


@login_required
def schedule_exam(request, exam_id):
    exam = get_object_or_404(Exam, id=exam_id)

    if request.method == 'POST':
        department_id = request.POST.get('department_id')
        class_level_id = request.POST.get('classgroup_id')
        course_id = request.POST.get('course_id')
        scheduled_date = request.POST.get('scheduled_date')
        start_time = request.POST.get('start_time')
        duration_minutes = request.POST.get('duration_minutes')
        total_questions = request.POST.get('total_questions')
        term = request.POST.get('term')

        # ✅ Step 1: Validate required fields
        if not (department_id and class_level_id and course_id and scheduled_date and start_time and duration_minutes and total_questions and term):
            return JsonResponse({'status': 'error', 'message': 'All fields are required.'})

        # ✅ Step 2: Convert numeric fields
        try:
            total_questions = int(total_questions)
            duration_minutes = int(duration_minutes)
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid numeric input.'})

        # ✅ Step 3: Check question count
        available_questions = Question.objects.filter(exam=exam).count()
        if total_questions > available_questions:
            return JsonResponse({
                'status': 'error',
                'message': f'You cannot schedule {total_questions} questions. '
                           f'Only {available_questions} question(s) exist for this exam.'
            })

        # ✅ Step 4: Fetch related objects
        department = get_object_or_404(Department, id=department_id)
        class_level = get_object_or_404(ClassGroup, id=class_level_id)
        course = get_object_or_404(Course, id=course_id)
        
        try:
            combined_str = f"{scheduled_date} {start_time}"
            naive_datetime = datetime.strptime(combined_str, "%Y-%m-%d %H:%M")
            aware_datetime = timezone.make_aware(naive_datetime, timezone.get_current_timezone())
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Invalid date/time format: {e}'})

        # ✅ Step 5: Check if schedule already exists for same exam, department, class, course & term
        existing_schedule = ExamSchedule.objects.filter(
            exam=exam,
            department=department,
            class_level=class_level,
            course_name=course,
            term=term
        ).first()

        if existing_schedule:
            # ✅ Update existing schedule
            existing_schedule.scheduled_date = scheduled_date
            existing_schedule.start_time = start_time
            existing_schedule.duration_minutes = duration_minutes
            existing_schedule.total_questions = total_questions
            existing_schedule.save()

            return JsonResponse({
                'status': 'updated',
                'message': 'Existing exam schedule updated successfully!'
            })
        else:
            # ✅ Create new schedule if none exists
            ExamSchedule.objects.create(
                exam=exam,
                department=department,
                class_level=class_level,
                course_name=course,
                scheduled_date=scheduled_date,
                start_time=start_time,
                duration_minutes=duration_minutes,
                total_questions=total_questions,
                created_by=request.user,
                term=term,
            )

            return JsonResponse({'status': 'success', 'message': 'Exam scheduled successfully!'})

    # ✅ GET request: load page
    departments = Department.objects.all()
    class_levels = ClassGroup.objects.all()

    return render(request, 'exam_details.html', {
        'exam': exam,
        'departments': departments,
        'class_levels': class_levels,
    })



# student dashboard and exam pick
from django.utils import timezone
@login_required
def student_portal(request):
    getLogo = schoollogo.objects.first()
    getTitle = title.objects.first()
    student = request.user.student_profile
    courses = student.courses.all()

    today = timezone.localdate()
    now = timezone.localtime().time()

    # ✅ Fetch all scheduled exams for student's department and class
    # exams = ExamSchedule.objects.filter(
    #     department=student.department,
    #     class_level__name__iexact=student.level_or_class
    # ).select_related('course_name', 'exam')
    print(student.level_or_class.id)
    

    exams = ExamSchedule.objects.filter(class_level=student.level_or_class, department=student.department)
    # ✅ Annotate each exam with its current status
    for exam in exams:
        if exam.scheduled_date == today and exam.start_time <= now:
            exam.status = "ongoing"
        elif exam.scheduled_date > today or (exam.scheduled_date == today and exam.start_time > now):
            exam.status = "upcoming"
        else:
            exam.status = "completed"

    # ✅ (Optional) Map each course to its exam
    course_exams = {}
    for course in courses:
        scheduled_exam = exams.filter(course_name=course).first()
        course_exams[course.id] = scheduled_exam
        
    
    print("Student level:", student.level_or_class, student.level_or_class.id)
    print("ExamSchedule levels:", ExamSchedule.objects.values_list('class_level_id', 'class_level__name'))
    print("Student department:", student.department_id)
    print("Exam departments:", ExamSchedule.objects.values_list('department_id', 'department__name'))


    return render(request, 'student_portal.html', {
        'student': student,
        'courses': courses,
        'getTitle': getTitle,
        'getLogo': getLogo,
        'exams': exams,
        'today': today,
        'now': now,
        'course_exams': course_exams,
    })
    
    
# import random
# @login_required
# def take_exam(request, course_id):
#     AggrePercentage = AgregatedPercentahe.objects.all().first()
#     getThePercent = AggrePercentage.scorePercent
#     import random
#     student = get_object_or_404(Student, user=request.user)

#     # ✅ Prevent multiple active exam sessions
#     if request.session.get('exam_in_progress') and request.session['exam_in_progress'] != course_id:
#         return render(request, "exam_not_found.html", {
#             "message": "You already have an active exam session in progress."
#         })
#     else:
#         request.session['exam_in_progress'] = course_id

#     # ✅ Fetch the scheduled exam for this course, department, and class
#     exam_schedule = ExamSchedule.objects.filter(
#         course_name_id=course_id,
#         department=student.department,
#         class_level=student.level_or_class
#     ).select_related('exam', 'course_name').first()

#     if not exam_schedule:
#         return render(request, "exam_not_found.html", {
#             "message": "No scheduled exam found for your class or department."
#         })

#     exam = exam_schedule.exam
#     questions = list(exam.questions.all())

#     # ✅ Handle no questions
#     if not questions:
#         return render(request, "exam_not_found.html", {
#             "message": f"No questions found for {exam.title}. Please contact your instructor."
#         })

#     # ✅ Randomize question order and options
#     random.shuffle(questions)
#     for q in questions:
#         options = [q.option_a, q.option_b, q.option_c, q.option_d]
#         random.shuffle(options)
#         q.shuffled_options = options

#     # ✅ Check if student already took this exam
#     existing_result = MarkedExam.objects.filter(student=student, exam=exam).first()
#     if existing_result:
#         return render(request, "exam_not_found.html", {
#             "message": f"You have already taken the exam: {exam.title}.",
#         })

#     if request.method == "POST":
#         answers = {}
#         score = 0

#         for question in questions:
#             selected = request.POST.get(f"question_{question.id}")
#             selected_answer = selected or "Not Answered"
#             answers[question.id] = selected_answer
#             if selected_answer == question.correct_answer:
#                 score += 1

#         total_questions = len(questions)
#         percentage = round((score / total_questions) * getThePercent, 2)

#         # ✅ Double-check no duplicate submission
#         if not MarkedExam.objects.filter(student=student, exam=exam).exists():
#             MarkedExam.objects.create(
#                 exam=exam,
#                 student=student,
#                 department=student.department,
#                 course=exam.course,
#                 exam_number=student.admission_number,
#                 username=student.user.username,
#                 full_name=student.full_name,
#                 total_score=score,
#                 total_questions=total_questions,
#                 percentage=percentage
#             )

#         # ✅ End session
#         request.session.pop('exam_in_progress', None)

#         return render(request, "exam_result.html", {
#             "exam": exam,
#             "questions": questions,
#             "answers": answers,
#             "score": score,
#             "total": total_questions,
#             "percentage": percentage,
#             "student": student,
#         })

#     # ✅ If GET request, render exam page
#     return render(request, "take_exam.html", {
#         "exam": exam,
#         "questions": questions,
#         "exam_schedule": exam_schedule,
#         "student": student,
#     })

import random
@login_required
def take_exam(request, course_id):
    # ✅ Get system configuration for scoring
    AggrePercentage = AgregatedPercentahe.objects.first()
    getThePercent = AggrePercentage.scorePercent if AggrePercentage else 100

    # ✅ Get current logged-in student
    student = get_object_or_404(Student, user=request.user)

    # ✅ Prevent multiple active exam sessions
    active_exam = request.session.get('exam_in_progress')
    if active_exam and active_exam != course_id:
        return render(request, "exam_not_found.html", {
            "message": "You already have an active exam session in progress."
        })
    else:
        request.session['exam_in_progress'] = course_id

    # ✅ Fetch the scheduled exam
    exam_schedule = ExamSchedule.objects.filter(
        course_name_id=course_id,
        department=student.department,
        class_level=student.level_or_class
    ).select_related('exam', 'course_name').first()

    if not exam_schedule:
        return render(request, "exam_not_found.html", {
            "message": "No scheduled exam found for your class or department."
        })

    exam = exam_schedule.exam
    questions = list(exam.questions.all())

    # ✅ Handle no questions
    if not questions:
        return render(request, "exam_not_found.html", {
            "message": f"No questions found for {exam.title}. Please contact your instructor."
        })

    # ✅ Randomize question and option order
    random.shuffle(questions)
    for q in questions:
        options = [q.option_a, q.option_b, q.option_c, q.option_d]
        random.shuffle(options)
        q.shuffled_options = options

    # ✅ Check if the student already took the exam
    if MarkedExam.objects.filter(student=student, exam=exam).exists():
        return render(request, "exam_not_found.html", {
            "message": f"You have already taken the exam: {exam.title}.",
        })

    # ✅ If student submits exam
    if request.method == "POST":
        score = 0
        answers = {}

        for question in questions:
            selected_answer = request.POST.get(f"question_{question.id}", "Not Answered")
            answers[question.id] = selected_answer

            if selected_answer == question.correct_answer:
                score += 1

        total_questions = len(questions)
        percentage = round((score / total_questions) * getThePercent, 2)

        # ✅ Double-check to avoid duplicate insertion
        if not MarkedExam.objects.filter(student=student, exam=exam).exists():
            MarkedExam.objects.create(
                exam=exam,
                student=student,
                department=student.department,
                course=exam.course,
                exam_number=student.admission_number,
                username=student.user.username,
                full_name=student.full_name,
                total_score=score,
                total_questions=total_questions,
                percentage=percentage,
            )

        # ✅ Clear session after exam completion
        request.session.pop('exam_in_progress', None)

        return render(request, "exam_result.html", {
            "exam": exam,
            "questions": questions,
            "answers": answers,
            "score": score,
            "total": total_questions,
            "percentage": percentage,
            "student": student,
        })

    # ✅ For GET request — render the exam page
    return render(request, "take_exam.html", {
        "exam": exam,
        "questions": questions,
        "exam_schedule": exam_schedule,
        "student": student,
    })



login_required
def exam_not_found(request):
    return render(request, 'exam_not_found.html')


from django.db import transaction
from django.db.models import Sum
@login_required
def student_score(request, student_id, course_id):
    AggrePercentage = AgregatedPercentahe.objects.first()
    getThePercent = AggrePercentage.scorePercent if AggrePercentage else 100

    student = get_object_or_404(Student, id=student_id)
    course = get_object_or_404(Course, id=course_id)
    scores = MarkedExam.objects.filter(student=student, course=course)\
        .select_related('course', 'exam', 'department')

    if request.method == 'POST':
        total_questions = int(request.POST.get('total_questions', 0))
        total_score = int(request.POST.get('total_score', 0))
        test_type = request.POST.get('test_type')
        # percentage = (total_score / total_questions) * getThePercent if total_questions > 0 else 0
        
        try:
            # ClassGroup is already stored on the student model
            class_instance = student.level_or_class
            print(class_instance)

            obj, created = TestScore.objects.update_or_create(
                student=student,
                course=course,
                department=student.department,
                class_group=str(student.level_or_class),  # ensure string
                test_type=test_type.strip(),              # ensure exact match
                defaults={
                    'total_questions': total_questions,
                    'total_score': total_score,
                }
            )


            return JsonResponse({'message': 'Score added successfully!'}, status=200)

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=400)
    
    exam_aggregates = scores.aggregate(
        total_score=Sum('total_score'),
        total_questions=Sum('total_questions')
    )

    exam_total_score = exam_aggregates['total_score'] or 0
    exam_total_questions = exam_aggregates['total_questions'] or 0

    exam_percentage = (exam_total_score / exam_total_questions * 70) if exam_total_questions > 0 else 0
    
    Testscores = TestScore.objects.filter(
        student=student,
        course=course
    ).select_related('course', 'department')

    aggregates = Testscores.aggregate(
        total_score_sum=Sum('total_score'),
        total_questions_sum=Sum('total_questions')
    )

    total_score_sum = aggregates['total_score_sum'] or 0
    total_questions_sum = aggregates['total_questions_sum'] or 0

    test_percentage = round((total_score_sum / total_questions_sum) * 30, 2) if total_questions_sum > 0 else 0
    total_percentage = exam_percentage + test_percentage
    print(Testscores)
    context = {
        'Testscores':Testscores,
        'total_score_sum':total_score_sum,
        'test_percentage': round(test_percentage,2),
        'total_percentage': round(total_percentage,2),
        'student': student, 
        'course': course, 
        'scores': scores
    }
    return render(request, 'studentScore.html', context)



@login_required
def export_student_scores_csv(request, student_id, course_id):
    student = get_object_or_404(Student, id=student_id)
    course = get_object_or_404(Course, id=course_id)

    # Fetch marked exams for this student and course
    scores = MarkedExam.objects.filter(student=student, course=course).select_related('exam', 'department', 'course')

    # Create the CSV response
    response = HttpResponse(
        content_type='text/csv',
        headers={'Content-Disposition': f'attachment; filename="{student.full_name}_marked_exams.csv"'},
    )

    writer = csv.writer(response)
    # CSV header
    writer.writerow([
        'S/N', 'Student Name', 'Exam Title', 'Course', 'Department',
        'Total Questions', 'Total Score', 'Percentage', 'Date Taken'
    ])

    # Write data rows
    for idx, score in enumerate(scores, start=1):
        writer.writerow([
            idx,
            score.full_name,
            score.exam.title if score.exam else "-",
            score.course.title if score.course else "-",
            score.department.name if score.department else "-",
            score.total_questions,
            score.total_score,
            f"{score.percentage:.2f}%",
            score.date_taken.strftime("%Y-%m-%d %H:%M"),
        ])

    return response


def CheckResult(request):
    getTitle = title.objects.all().first()
    getLogo = schoollogo.objects.all().first()
    GetAboutSchool = AboutSchool.objects.all().first()
    student = None
    results = None
    error = None

    if request.method == "POST":
        form = ResultCheckForm(request.POST)
        if form.is_valid():
            admission_number = form.cleaned_data["admission_number"]
            access_code = form.cleaned_data["access_code"]

            try:
                # ✅ Verify student
                student = Student.objects.get(admission_number=admission_number)

                # ✅ Verify access code (OneToOne relation)
                access = ResultAccessCode.objects.get(students=student, code=access_code)

                # ✅ Fetch the student's marked exams
                results = MarkedExam.objects.filter(student=student).select_related('exam', 'course', 'department')

                if not results.exists():
                    error = "No results found for this student."

            except Student.DoesNotExist:
                error = "Invalid Admission Number."
            except ResultAccessCode.DoesNotExist:
                error = "Invalid Access Code for this student."

    else:
        form = ResultCheckForm()

    context = {
        'getTitle': getTitle,
        'getLogo': getLogo,
        'AboutSchool': GetAboutSchool,
        'form': form,
        'student': student,
        'results': results,
        'error': error,
    }
    return render(request, 'checkResult.html', context)
