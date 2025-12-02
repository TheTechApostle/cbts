from django.urls import path
from . import views


# urlpatterns = [
#     # ----------------------------
#     # 🏠 Home & Authentication
#     # ----------------------------
#     path('', views.MyHome, name='MyHome'),
#     path('login/', views.LoginUser, name='LoginUser'),

#     # ----------------------------
#     # 🎓 Student Routes
#     # ----------------------------
#     path('register/student/', views.register_student, name='register_student'),
#     path('register/student/SuccessPage/', views.SuccessPage, name='SuccessPage'),
#     path('CBT/student/dashboard/', views.dashboard, name='dashboard'),
#     path('portal/', views.student_portal, name='student_portal'),

#     # ----------------------------
#     # 👩‍🏫 Teacher Routes
#     # ----------------------------
#     path('CBT/Teacherdashboard/', views.Teacherdashboard, name='Teacherdashboard'),
#     path('CBT/Teacherdashboard/manage-course/', views.teacher_manage_course, name='teacher_manage_course'),

#     # Add or edit exam questions
#     path('CBT/Teacherdashboard/add-questions/', views.add_questions, name='add_questions'),
#     path('CBT/Teacherdashboard/add-questions/<int:exam_id>/', views.add_questions, name='add_questions_with_id'),

#     # ----------------------------
#     # 🧾 Exam Management (Teacher)
#     # ----------------------------
#     path('exam/detail/<int:exam_id>/', views.exam_detail, name='exam_detail'),
#     path('exam/<int:exam_id>/schedule/', views.schedule_exam, name='schedule_exam'),
#     path('exam/<int:exam_id>/edit-question/', views.edit_question, name='edit_question'),
#     path('exam/not-found/', views.exam_not_found, name='exam_not_found'),

#     # ----------------------------
#     # 🧑‍🎓 Student Exam Participation
#     # ----------------------------
#     path('exam/take/<int:course_id>/', views.take_exam, name='take_exam'),
# ]



urlpatterns = [
    path('', views.MyHome, name='MyHome'),
    path('register/student/', views.register_student, name='register_student'),
    path('e_learning/student/', views.lecture_list, name='lecture_list'),
    path("lectures/upload/", views.lecture_upload, name="lecture_upload"),
    path("lectures/toggle/", views.lecture_toggle_status, name="lecture_toggle_status"),
    path("lectures/delete/", views.lecture_delete, name="lecture_delete"),
    path("lectures/export/", views.export_lectures_csv, name="export_lectures_csv"),
    path("lectures/<int:pk>/preview/", views.lecture_preview, name="lecture_preview"), 
    path("Elerning/student/dashboard/", views.student_dashboard, name="student_dashboard"),
    path("lectures/<int:pk>/view/", views.lecture_student_view, name="lecture_student_view"),
    path("lectures/<int:pk>/vote/", views.lecture_vote, name="lecture_vote"),
    path("student_courses/<int:course_id>/", views.course_detail, name="course_detail"),
    path('teachers/teacher_list', views.teacher_list, name='teacher_list'),
    path('logout/', views.logout_user, name='logout_user'),
    path('register/Teacher/', views.register_teacher, name='register_teacher'),
    path('ajax/load-classgroups/', views.load_classgroups, name='ajax_load_classgroups'),
    path('ajax/load-courses/', views.load_courses, name='ajax_load_courses'),
    path('register/student/SuccessPage', views.SuccessPage, name='SuccessPage'),
    path('CBT/student/dashboard', views.dashboard, name='dashboard'),
    path('CBT/Teacherdashboard', views.Teacherdashboard, name='Teacherdashboard'),
    path('exams/<int:exam_id>/add-questions/', views.add_questions, name='add_questions'),
    path('CBT/Teacherdashboard/add_questions', views.add_questions, name='add_questions'),
    path('portal/', views.student_portal, name='student_portal'),
      # Page to start exam
    path('CBT/Teacherdashboard/teacher_manage_course', views.teacher_manage_course, name='teacher_manage_course'),
    path('exam/<int:exam_id>/', views.exam_detail, name='exam_detail'),
    path('examStudent/<int:classgroup_id>/course/<int:course_id>/', views.MyStudent, name='myStudent'),
    path('question/edit/', views.edit_question, name='edit_question'),
    path('exam/<int:exam_id>/schedule/', views.schedule_exam, name='schedule_exam'),
    path('login/', views.LoginUser, name="LoginUser"),
    path('exam/exam_not_found', views.exam_not_found, name="exam_not_found"),
    path('takeexam/<int:course_id>/', views.take_exam, name='take_exam'),
    path('exam/<int:exam_id>/publish/', views.publish_exam, name='publish_exam'),
    path('Student/ResultCheck', views.CheckResult, name='CheckResult'),
    # urls.py
    path('students/<int:student_id>/scores/<int:course_id>/', views.student_score, name='student_score'),
    path('student/<int:student_id>/course/<int:course_id>/export_csv/', 
         views.export_student_scores_csv, name='export_student_scores_csv'),


]
