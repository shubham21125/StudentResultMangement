from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg
from django.http import JsonResponse, StreamingHttpResponse
from django.core.mail import send_mail
from django.urls import reverse
from django.conf import settings

from datetime import datetime, timedelta, date
import os
import pickle
import numpy as np

from .models import (
    Notice, Student, Subject, Class, SubjectCombination,
    Result, Parent, Attendance, ProgressReport
)


# ==================== HOMEPAGE ====================

def index(request):
    notices = Notice.objects.all().order_by('-id')
    total_students = Student.objects.count()
    total_subjects = Subject.objects.count()
    total_classes = Class.objects.count()
    total_results = Result.objects.values('student').distinct().count()
    return render(request, 'index.html', {
        'notices': notices,
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_classes': total_classes,
        'total_results': total_results,
    })


def notice_detail(request, notice_id):
    notice = get_object_or_404(Notice, id=notice_id)
    return render(request, 'notice_detail.html', {'notice': notice})


# ==================== ADMIN AUTH ====================

def admin_login(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('admin_dashboard')
    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            error = "Invalid credentials or not authorized."
    return render(request, 'admin_login.html', {'error': error})


@login_required
def admin_dashboard(request):
    total_students = Student.objects.count()
    total_subjects = Subject.objects.count()
    total_classes = Class.objects.count()
    total_results = Result.objects.values('student').distinct().count()
    return render(request, 'admin_dashboard.html', {
        'total_students': total_students,
        'total_subjects': total_subjects,
        'total_classes': total_classes,
        'total_results': total_results,
    })


def admin_logout(request):
    logout(request)
    return redirect('admin_login')


# ==================== CLASS MANAGEMENT ====================

@login_required
def create_class(request):
    if request.method == 'POST':
        try:
            class_name = request.POST.get('classname')
            class_numeric = request.POST.get('classnamenumeric')
            section = request.POST.get('section')
            Class.objects.create(class_name=class_name, class_numeric=class_numeric, section=section)
            messages.success(request, "Class created successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('create_class')
    return render(request, 'create_class.html')


@login_required
def manage_classes(request):
    if request.method == 'POST' and request.POST.get('delete'):
        try:
            class_obj = get_object_or_404(Class, id=request.POST.get('delete'))
            class_obj.delete()
            messages.success(request, "Class deleted successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('manage_classes')

    classes = Class.objects.all()
    return render(request, 'manage_classes.html', {'classes': classes})


@login_required
def edit_class(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    if request.method == 'POST':
        try:
            class_obj.class_name = request.POST.get('classname')
            class_obj.class_numeric = request.POST.get('classnamenumeric')
            class_obj.section = request.POST.get('section')
            class_obj.save()
            messages.success(request, "Class updated successfully!")
            return redirect('manage_classes')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
    return render(request, 'edit_class.html', {'class_obj': class_obj})


# ==================== SUBJECT MANAGEMENT ====================

@login_required
def create_subject(request):
    if request.method == 'POST':
        try:
            Subject.objects.create(
                subject_name=request.POST.get('subjectname'),
                subject_code=request.POST.get('subjectcode'),
            )
            messages.success(request, "Subject created successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('create_subject')
    return render(request, 'create_subject.html')


@login_required
def manage_subject(request):
    if request.method == 'POST' and request.POST.get('delete'):
        try:
            subject_obj = get_object_or_404(Subject, id=request.POST.get('delete'))
            subject_obj.delete()
            messages.success(request, "Subject deleted successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('manage_subject')

    subjects = Subject.objects.all()
    return render(request, 'manage_subject.html', {'subjects': subjects})


@login_required
def edit_subject(request, subject_id):
    subject_obj = get_object_or_404(Subject, id=subject_id)
    if request.method == 'POST':
        try:
            subject_obj.subject_name = request.POST.get('subjectname')
            subject_obj.subject_code = request.POST.get('subjectcode')
            subject_obj.save()
            messages.success(request, "Subject updated successfully!")
            return redirect('manage_subject')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
    return render(request, 'edit_subject.html', {'subject_obj': subject_obj})


# ==================== SUBJECT COMBINATIONS ====================

@login_required
def add_subject_combination(request):
    classes = Class.objects.all()
    subjects = Subject.objects.all()
    if request.method == 'POST':
        try:
            class_id = request.POST.get('class')
            subject_id = request.POST.get('subject')
            SubjectCombination.objects.create(student_class_id=class_id, subject_id=subject_id, status=1)
            messages.success(request, "Subject combination created successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('add_subject_combination')
    return render(request, 'add_subject_combination.html', {'classes': classes, 'subjects': subjects})


@login_required
def manage_subject_combination(request):
    if request.method == 'POST':
        aid = request.POST.get('aid')
        did = request.POST.get('did')
        try:
            if aid:
                SubjectCombination.objects.filter(id=aid).update(status=1)
                messages.success(request, "Subject combination activated successfully!")
            elif did:
                SubjectCombination.objects.filter(id=did).update(status=0)
                messages.success(request, "Subject combination deactivated successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('manage_subject_combination')

    combinations = SubjectCombination.objects.all()
    return render(request, 'manage_subject_combination.html', {'combinations': combinations})


# ==================== STUDENT MANAGEMENT ====================

@login_required
def add_student(request):
    classes = Class.objects.all()
    if request.method == 'POST':
        try:
            student_class = get_object_or_404(Class, id=request.POST.get('class'))
            Student.objects.create(
                name=request.POST.get('fullname'),
                roll_id=request.POST.get('rollid'),
                email=request.POST.get('emailid'),
                gender=request.POST.get('gender'),
                dob=request.POST.get('dob'),
                student_class=student_class,
            )
            messages.success(request, "Student info added successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('add_student')
    return render(request, 'add_student.html', {'classes': classes})


@login_required
def manage_students(request):
    students = Student.objects.all()
    return render(request, 'manage_students.html', {'students': students})


@login_required
def edit_student(request, student_id):
    student_obj = get_object_or_404(Student, id=student_id)
    if request.method == 'POST':
        try:
            student_obj.name = request.POST.get('fullname')
            student_obj.roll_id = request.POST.get('rollid')
            student_obj.email = request.POST.get('emailid')
            student_obj.gender = request.POST.get('gender')
            student_obj.dob = request.POST.get('dob')
            student_obj.status = int(request.POST.get('status'))
            student_obj.save()
            messages.success(request, "Student updated successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('manage_students')
    return render(request, 'edit_student.html', {'student_obj': student_obj})


# ==================== NOTICE MANAGEMENT ====================

@login_required
def add_notice(request):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            details = request.POST.get('details')
            Notice.objects.create(title=title, detail=details)

            all_student_emails = list(Student.objects.filter(status=1).values_list('email', flat=True))
            all_parent_emails = list(
                Parent.objects.select_related('user').values_list('user__email', flat=True)
            )
            all_emails = list(filter(None, set(all_student_emails + all_parent_emails)))

            if all_emails:
                send_mail(
                    subject=f'New Notice: {title} - SRMS',
                    message=(
                        f'Dear Student/Parent,\n\nA new notice has been posted:\n\n'
                        f'Title: {title}\n\n{details}\n\n'
                        'Please visit the school portal for more details.\n\nRegards,\nSRMS College'
                    ),
                    from_email=None,
                    recipient_list=all_emails,
                    fail_silently=True,
                )

            messages.success(request, "Notice added successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
    return render(request, 'add_notice.html')


@login_required
def manage_notice(request):
    if request.method == 'POST' and request.POST.get('delete'):
        try:
            notice_obj = get_object_or_404(Notice, id=request.POST.get('delete'))
            notice_obj.delete()
            messages.success(request, "Notice deleted successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('manage_notice')

    notices = Notice.objects.all()
    return render(request, 'manage_notice.html', {'notices': notices})


# ==================== RESULT MANAGEMENT ====================

@login_required
def add_result(request):
    classes = Class.objects.all()
    if request.method == 'POST':
        try:
            class_id = request.POST.get('class')
            student_id = request.POST.get('studentid')
            marks_data = {
                key.split('_')[1]: value
                for key, value in request.POST.items()
                if key.startswith('marks_')
            }
            for subject_id, marks in marks_data.items():
                Result.objects.create(
                    student_id=student_id,
                    student_class_id=class_id,
                    subject_id=subject_id,
                    marks=int(marks),
                )

            student = get_object_or_404(Student, id=student_id)

            if student.email:
                send_mail(
                    subject='Your Result Has Been Added - SRMS',
                    message=(
                        f'Dear {student.name},\n\nYour result has been added successfully by the school.\n\n'
                        'Please visit the school portal to check your full result.\n\n'
                        f'Roll ID: {student.roll_id}\nClass: {student.student_class}\n\nRegards,\nSRMS College'
                    ),
                    from_email=None,
                    recipient_list=[student.email],
                    fail_silently=True,
                )

            for parent in Parent.objects.filter(student=student).select_related('user'):
                if parent.user.email:
                    send_mail(
                        subject=f'Result Added for {student.name} - SRMS',
                        message=(
                            f'Dear {parent.user.get_full_name()},\n\n'
                            f'The result for your child {student.name} has been added.\n\n'
                            'Please login to the parent portal to view the full result.\n\nRegards,\nSRMS College'
                        ),
                        from_email=None,
                        recipient_list=[parent.user.email],
                        fail_silently=True,
                    )

            messages.success(request, "Result info added successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('add_result')
    return render(request, 'add_result.html', {'classes': classes})


def get_students_subjects(request):
    class_id = request.GET.get('class_id')
    if class_id:
        students = list(Student.objects.filter(student_class_id=class_id).values('id', 'name', 'roll_id'))
        subject_combinations = SubjectCombination.objects.filter(
            student_class_id=class_id, status=1
        ).select_related('subject')
        subjects = [{'id': sc.subject.id, 'name': sc.subject.subject_name} for sc in subject_combinations]
        return JsonResponse({'students': students, 'subjects': subjects})
    return JsonResponse({'students': [], 'subjects': []})


@login_required
def manage_result(request):
    results = Result.objects.select_related('student', 'student_class').all()
    students = {}
    for res in results:
        stu_id = res.student.id
        if stu_id not in students:
            students[stu_id] = {
                'student': res.student,
                'class': res.student_class,
            }
    return render(request, 'manage_result.html', {'results': students.values()})


@login_required
def edit_result(request, stid):
    student = get_object_or_404(Student, id=stid)
    results = Result.objects.filter(student=student)

    if request.method == 'POST':
        ids = request.POST.getlist('id[]')
        marks_list = request.POST.getlist('marks[]')
        for i in range(len(ids)):
            result_obj = get_object_or_404(Result, id=ids[i])
            result_obj.marks = int(marks_list[i])
            result_obj.save()

        if student.email:
            send_mail(
                subject='Your Result Has Been Updated - SRMS',
                message=(
                    f'Dear {student.name},\n\nYour result has been updated by the school.\n\n'
                    'Please visit the school portal to check your updated result.\n\n'
                    f'Roll ID: {student.roll_id}\nClass: {student.student_class}\n\nRegards,\nSRMS College'
                ),
                from_email=None,
                recipient_list=[student.email],
                fail_silently=True,
            )

        for parent in Parent.objects.filter(student=student).select_related('user'):
            if parent.user.email:
                send_mail(
                    subject=f'Result Updated for {student.name} - SRMS',
                    message=(
                        f'Dear {parent.user.get_full_name()},\n\n'
                        f'The result for your child {student.name} has been updated.\n\n'
                        'Please login to the parent portal to view the updated result.\n\nRegards,\nSRMS College'
                    ),
                    from_email=None,
                    recipient_list=[parent.user.email],
                    fail_silently=True,
                )

        messages.success(request, "Results updated successfully!")
        return redirect('manage_result')
    return render(request, 'edit_result.html', {'student': student, 'results': results})


# ==================== PASSWORD CHANGE ====================

@login_required
def change_password(request):
    if request.method == 'POST':
        old = request.POST.get('old_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')

        if new != confirm:
            messages.error(request, "New password and confirm password do not match.")
            return redirect('change_password')

        user = authenticate(username=request.user.username, password=old)
        if user:
            user.set_password(new)
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully!")
            return redirect('change_password')
        else:
            messages.error(request, "Old password is incorrect.")

    return render(request, 'change_password.html')


# ==================== PASS/FAIL LOGIC ====================

def get_grade(percentage, is_failed):
    if is_failed:
        return 'F'
    elif percentage >= 90:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 70:
        return 'B+'
    elif percentage >= 60:
        return 'B'
    elif percentage >= 50:
        return 'C+'
    elif percentage >= 35:
        return 'C'
    else:
        return 'F'


def search_result(request):
    classes = Class.objects.all()
    return render(request, 'search_result.html', {'classes': classes})


def check_result(request):
    if request.method == 'POST':
        rollid = request.POST.get('rollid')
        class_id = request.POST.get('class')
        try:
            student = Student.objects.get(roll_id=rollid, student_class_id=class_id)
            results = Result.objects.filter(student=student)

            if not results.exists():
                messages.error(request, "No result found for the provided Roll ID and Class.")
                return redirect('search_result')

            total_marks = sum(r.marks for r in results)
            subject_count = results.count()
            max_total = subject_count * 100
            percentage = round((total_marks / max_total) * 100 if max_total > 0 else 0, 2)

            failed_subjects = [r for r in results if r.marks < 35]
            passed_subjects = [r for r in results if r.marks >= 35]
            is_failed = len(failed_subjects) > 0
            grade = get_grade(percentage, is_failed)

            return render(request, 'result_page.html', {
                'student': student,
                'results': results,
                'total_marks': total_marks,
                'subject_count': subject_count,
                'max_total': max_total,
                'percentage': percentage,
                'failed_subjects': failed_subjects,
                'passed_subjects': passed_subjects,
                'is_failed': is_failed,
                'grade': grade,
            })

        except Student.DoesNotExist:
            messages.error(request, "No result found for the provided Roll ID and Class.")
            return redirect('search_result')
        except Exception:
            messages.error(request, "Something went wrong. Please try again.")
            return redirect('search_result')

    return redirect('search_result')


def get_student_percentage(request):
    student_id = request.GET.get('student_id')
    if not student_id:
        return JsonResponse({'percentage': None, 'grade': 'N/A'})
    try:
        student = Student.objects.get(id=student_id)
        results = Result.objects.filter(student=student)
        if not results.exists():
            return JsonResponse({'percentage': None, 'grade': 'N/A'})
        total_marks = sum(r.marks for r in results)
        max_total = results.count() * 100
        percentage = round((total_marks / max_total) * 100 if max_total > 0 else 0, 2)
        failed_subjects = [r for r in results if r.marks < 35]
        is_failed = len(failed_subjects) > 0
        return JsonResponse({'percentage': percentage, 'grade': get_grade(percentage, is_failed)})
    except Student.DoesNotExist:
        return JsonResponse({'percentage': None, 'grade': 'N/A'})
    except Exception as e:
        return JsonResponse({'percentage': None, 'grade': 'N/A', 'error': str(e)})


# ==================== PARENT PORTAL ====================

def parent_login(request):
    if request.user.is_authenticated:
        if Parent.objects.filter(user=request.user).exists():
            return redirect('parent_dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            if Parent.objects.filter(user=user).exists():
                login(request, user)
                messages.success(request, f'Welcome {user.get_full_name()}!')
                return redirect('parent_dashboard')
            else:
                messages.error(request, 'This account is not registered as a parent.')
        else:
            messages.error(request, 'Invalid username or password.')

    return render(request, 'parent/login.html')


def parent_logout(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('home')


@login_required(login_url='parent_login')
def parent_dashboard(request):
    try:
        parent = Parent.objects.get(user=request.user)
        student = parent.student

        thirty_days_ago = datetime.now().date() - timedelta(days=30)
        total_days = Attendance.objects.filter(student=student, date__gte=thirty_days_ago).count()
        present_days = Attendance.objects.filter(
            student=student, date__gte=thirty_days_ago, status='present'
        ).count()
        attendance_percentage = round((present_days / total_days * 100) if total_days > 0 else 0, 2)

        all_results = Result.objects.filter(student=student)
        recent_results = all_results.order_by('-posting_date')[:5]
        latest_progress = ProgressReport.objects.filter(student=student).order_by('-created_at').first()
        avg_marks = all_results.aggregate(Avg('marks'))['marks__avg'] or 0
        failed_subjects = [r for r in all_results if r.marks < 35]

        return render(request, 'parent/dashboard.html', {
            'parent': parent,
            'student': student,
            'total_days': total_days,
            'present_days': present_days,
            'attendance_percentage': attendance_percentage,
            'recent_results': recent_results,
            'latest_progress': latest_progress,
            'avg_marks': round(avg_marks, 2),
            'is_failed': len(failed_subjects) > 0,
            'failed_subjects': failed_subjects,
        })
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('parent_login')


@login_required(login_url='parent_login')
def parent_view_attendance(request):
    try:
        parent = Parent.objects.get(user=request.user)
        student = parent.student

        selected_month = request.GET.get('month', datetime.now().month)
        selected_year = request.GET.get('year', datetime.now().year)

        attendance_records = Attendance.objects.filter(
            student=student,
            date__month=selected_month,
            date__year=selected_year
        ).order_by('-date')

        return render(request, 'parent/attendance.html', {
            'student': student,
            'attendance_records': attendance_records,
            'total_records': attendance_records.count(),
            'present_count': attendance_records.filter(status='present').count(),
            'absent_count': attendance_records.filter(status='absent').count(),
            'late_count': attendance_records.filter(status='late').count(),
            'selected_month': selected_month,
            'selected_year': selected_year,
        })
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('parent_login')


@login_required(login_url='parent_login')
def parent_view_results(request):
    try:
        parent = Parent.objects.get(user=request.user)
        student = parent.student
        results = Result.objects.filter(student=student).select_related('subject').order_by('-posting_date')

        failed_subjects = [r for r in results if r.marks < 35]
        passed_subjects = [r for r in results if r.marks >= 35]
        is_failed = len(failed_subjects) > 0

        if results.exists():
            total_marks = sum(r.marks for r in results)
            max_marks = len(results) * 100
            percentage = round((total_marks / max_marks * 100) if max_marks > 0 else 0, 2)
            avg_marks = results.aggregate(Avg('marks'))['marks__avg'] or 0
            grade = get_grade(percentage, is_failed)
        else:
            total_marks = max_marks = percentage = avg_marks = 0
            grade = 'N/A'

        return render(request, 'parent/results.html', {
            'student': student,
            'results': results,
            'total_marks': total_marks,
            'max_marks': max_marks,
            'percentage': percentage,
            'avg_marks': round(avg_marks, 2),
            'failed_subjects': failed_subjects,
            'passed_subjects': passed_subjects,
            'is_failed': is_failed,
            'grade': grade,
        })
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('parent_login')


@login_required(login_url='parent_login')
def parent_view_progress(request):
    try:
        parent = Parent.objects.get(user=request.user)
        student = parent.student
        progress_reports = ProgressReport.objects.filter(student=student).order_by('-created_at')
        return render(request, 'parent/progress.html', {
            'student': student,
            'progress_reports': progress_reports,
        })
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('parent_login')


@login_required(login_url='parent_login')
def parent_profile(request):
    try:
        parent = Parent.objects.get(user=request.user)
        return render(request, 'parent/profile.html', {
            'parent': parent,
            'student': parent.student,
        })
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('parent_login')


# ==================== PARENT ACCOUNT MANAGEMENT ====================

@login_required
def create_parent_account(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        student_id = request.POST.get('student')
        relationship = request.POST.get('relationship')

        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            student = get_object_or_404(Student, id=student_id)
            Parent.objects.create(
                user=user,
                phone=phone,
                address=address,
                student=student,
                relationship=relationship,
            )

            if email:
                login_url = request.build_absolute_uri(reverse('parent_login'))
                send_mail(
                    subject='Your Parent Account Has Been Created - SRMS',
                    message=(
                        f'Dear {first_name} {last_name},\n\n'
                        'Your parent account has been created successfully.\n\n'
                        f'Username: {username}\n'
                        f'Login URL: {login_url}\n\n'
                        'Please use the password set by the administrator to log in. '
                        'You can change it after your first login.\n\n'
                        f'You can now track the following for {student.name}:\n'
                        '- Results & Marks\n- Attendance\n- Progress Reports\n\n'
                        'Regards,\nSRMS College'
                    ),
                    from_email=None,
                    recipient_list=[email],
                    fail_silently=True,
                )

            messages.success(request, f'Parent account created successfully for {student.name}')
            return redirect('manage_parents')
        except Exception as e:
            messages.error(request, f'Error creating parent account: {str(e)}')

    students = Student.objects.filter(status=1)
    return render(request, 'admin/create_parent.html', {'students': students})


@login_required
def manage_parents(request):
    if request.method == 'POST' and request.POST.get('delete'):
        try:
            parent_obj = get_object_or_404(Parent, id=request.POST.get('delete'))
            user = parent_obj.user
            parent_obj.delete()
            user.delete()
            messages.success(request, "Parent account deleted successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('manage_parents')

    parents = Parent.objects.all().select_related('user', 'student')
    return render(request, 'admin/manage_parents.html', {'parents': parents})


# ==================== ATTENDANCE ====================

@login_required
def add_attendance(request):
    classes = Class.objects.all()
    if request.method == 'POST':
        try:
            class_id = request.POST.get('class')
            date_str = request.POST.get('date')
            students = Student.objects.filter(student_class_id=class_id)

            for student in students:
                status = request.POST.get(f'status_{student.id}')
                remarks = request.POST.get(f'remarks_{student.id}', '')

                Attendance.objects.update_or_create(
                    student=student,
                    date=date_str,
                    defaults={'status': status, 'remarks': remarks},
                )

                if status == 'absent':
                    for parent in Parent.objects.filter(student=student).select_related('user'):
                        if parent.user.email:
                            send_mail(
                                subject=f'Attendance Alert: {student.name} was Absent - SRMS',
                                message=(
                                    f'Dear {parent.user.get_full_name()},\n\n'
                                    f'Your child {student.name} was marked ABSENT on {date_str}.\n\n'
                                    f'Remarks: {remarks if remarks else "No remarks"}\n\n'
                                    'Please contact the school if you have any questions.\n\nRegards,\nSRMS School'
                                ),
                                from_email=None,
                                recipient_list=[parent.user.email],
                                fail_silently=True,
                            )

            messages.success(request, "Attendance recorded successfully!")
            return redirect('add_attendance')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")

    return render(request, 'admin/add_attendance.html', {'classes': classes})


# ==================== PROGRESS REPORTS ====================

@login_required
def add_progress_report(request):
    students = Student.objects.filter(status=1)
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student')
            term = request.POST.get('term')
            overall_percentage = request.POST.get('overall_percentage')
            grade = request.POST.get('grade')
            teacher_remarks = request.POST.get('teacher_remarks')
            strengths = request.POST.get('strengths')
            areas_of_improvement = request.POST.get('areas_of_improvement')

            ProgressReport.objects.create(
                student_id=student_id,
                term=term,
                overall_percentage=overall_percentage,
                grade=grade,
                teacher_remarks=teacher_remarks,
                strengths=strengths,
                areas_of_improvement=areas_of_improvement,
            )

            student = get_object_or_404(Student, id=student_id)
            for parent in Parent.objects.filter(student=student).select_related('user'):
                if parent.user.email:
                    send_mail(
                        subject=f'Progress Report Added - {term} - SRMS',
                        message=(
                            f'Dear {parent.user.get_full_name()},\n\n'
                            f'A new progress report has been added for {student.name}.\n\n'
                            f'Term: {term}\nGrade: {grade}\nOverall Percentage: {overall_percentage}%\n'
                            f'Teacher Remarks: {teacher_remarks}\n'
                            f'Strengths: {strengths or "N/A"}\n'
                            f'Areas of Improvement: {areas_of_improvement or "N/A"}\n\n'
                            'Please login to the parent portal for more details.\n\nRegards,\nSRMS College'
                        ),
                        from_email=None,
                        recipient_list=[parent.user.email],
                        fail_silently=True,
                    )

            messages.success(request, "Progress report added successfully!")
            return redirect('add_progress_report')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")

    return render(request, 'admin/add_progress_report.html', {'students': students})


# ==================== FACE RECOGNITION ====================

# Module-level cache: loaded once on startup, refreshed after training.
_face_recognition_data = {'encodings': [], 'ids': []}


def _get_encodings_dir():
    return os.path.join(settings.MEDIA_ROOT, 'face_encodings')


def _get_all_encodings_path():
    return os.path.join(_get_encodings_dir(), 'all_encodings.pkl')


def _load_face_recognition_data():
    """Load the combined encodings file into the module-level cache."""
    global _face_recognition_data
    path = _get_all_encodings_path()
    if os.path.exists(path):
        with open(path, 'rb') as f:
            data = pickle.load(f)
        # Support both storage formats:
        #   new format (file 2): {'encodings': [...], 'ids': [...]}
        #   old format (file 1): {student_id: encoding, ...}
        if isinstance(data, dict) and 'encodings' in data:
            _face_recognition_data['encodings'] = data['encodings']
            _face_recognition_data['ids'] = data['ids']
        else:
            _face_recognition_data['encodings'] = list(data.values())
            _face_recognition_data['ids'] = list(data.keys())
    else:
        _face_recognition_data = {'encodings': [], 'ids': []}


# Load on import so the live feed is ready immediately.
_load_face_recognition_data()


@login_required
def face_register(request):
    """Save a student photo and compute + store their face encoding."""
    students = Student.objects.filter(status=1)

    if request.method == 'POST':
        student_id = request.POST.get('student_id') or request.POST.get('student')
        photo = request.FILES.get('photo')

        if not student_id or not photo:
            messages.error(request, "Please select a student and upload a photo.")
            return render(request, 'admin/face_register.html', {'students': students})

        try:
            import face_recognition as fr

            student = get_object_or_404(Student, id=student_id)
            student.photo = photo
            student.save()

            image = fr.load_image_file(student.photo.path)
            encodings = fr.face_encodings(image)

            if not encodings:
                # Clean up the unusable photo
                student.photo.delete(save=False)
                student.save()
                messages.warning(
                    request,
                    f"Photo saved for {student.name}, but no face was detected. "
                    "Please upload a clearer front-facing photo."
                )
                return redirect('face_register')

            enc_dir = _get_encodings_dir()
            os.makedirs(enc_dir, exist_ok=True)
            with open(os.path.join(enc_dir, f'{student.id}.pkl'), 'wb') as f:
                pickle.dump(encodings[0], f)

            messages.success(
                request,
                f"Face registered successfully for {student.name}! "
                "Run 'Train All Faces' to update the recognition model."
            )

        except ImportError:
            messages.warning(
                request,
                f"Photo saved for {student.name}, but the face_recognition library is not installed. "
                "Run: pip install face-recognition opencv-python"
            )
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")

        return redirect('face_register')

    return render(request, 'admin/face_register.html', {'students': students})


@login_required
def face_train(request):
    """Re-encode all student photos and rebuild the combined encodings file."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST required'}, status=405)

    try:
        import face_recognition as fr

        known_encodings = []
        known_ids = []
        enc_dir = _get_encodings_dir()
        os.makedirs(enc_dir, exist_ok=True)

        for student in Student.objects.filter(status=1).exclude(photo=''):
            if not student.photo:
                continue
            try:
                img_path = student.photo.path
                if not os.path.exists(img_path):
                    continue
                encodings = fr.face_encodings(fr.load_image_file(img_path))
                if encodings:
                    known_encodings.append(encodings[0])
                    known_ids.append(student.id)
                    # Also persist individual encoding for quick per-student lookup
                    with open(os.path.join(enc_dir, f'{student.id}.pkl'), 'wb') as f:
                        pickle.dump(encodings[0], f)
            except Exception:
                continue

        # Persist combined file using the new dict format
        with open(_get_all_encodings_path(), 'wb') as f:
            pickle.dump({'encodings': known_encodings, 'ids': known_ids}, f)

        # Refresh the in-memory cache immediately
        _load_face_recognition_data()

        return JsonResponse({
            'status': 'success',
            'message': f'Training complete. {len(known_ids)} student(s) encoded.'
        })

    except ImportError:
        return JsonResponse({
            'status': 'error',
            'message': 'face_recognition library not installed. Run: pip install face-recognition opencv-python'
        }, status=500)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


def _generate_frames():
    """
    Generator that yields MJPEG frames from the default webcam,
    annotating each detected face with the matched student's name.
    Uses the module-level _face_recognition_data cache.
    """
    try:
        import cv2
        import face_recognition as fr
    except ImportError:
        return

    known_encodings = _face_recognition_data['encodings']
    known_ids = _face_recognition_data['ids']
    id_name = {s.id: s.name for s in Student.objects.filter(status=1)}

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            # Scale down for faster recognition, then scale coords back up
            small = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small = cv2.cvtColor(small, cv2.COLOR_BGR2RGB)

            face_locations = fr.face_locations(rgb_small)
            face_encodings = fr.face_encodings(rgb_small, face_locations)

            for (top, right, bottom, left), enc in zip(face_locations, face_encodings):
                top *= 4; right *= 4; bottom *= 4; left *= 4
                name, color = "Unknown", (0, 0, 255)

                if known_encodings:
                    distances = fr.face_distance(known_encodings, enc)
                    best_idx = int(np.argmin(distances))
                    if distances[best_idx] < 0.6:
                        name = id_name.get(known_ids[best_idx], f"ID:{known_ids[best_idx]}")
                        color = (0, 200, 0)

                cv2.rectangle(frame, (left, top), (right, bottom), color, 2)
                cv2.rectangle(frame, (left, bottom - 28), (right, bottom), color, cv2.FILLED)
                cv2.putText(
                    frame, name, (left + 4, bottom - 8),
                    cv2.FONT_HERSHEY_DUPLEX, 0.6, (255, 255, 255), 1
                )

            _, buffer = cv2.imencode('.jpg', frame)
            yield b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n'
    finally:
        cap.release()


@login_required
def live_feed(request):
    return StreamingHttpResponse(
        _generate_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )


@login_required
def face_detect_attendance(request):
    """
    GET  – render the face attendance form.
    POST – receive a list of detected student IDs, mark present/absent,
           and email parents of absent students.
    """
    classes = Class.objects.all()

    if request.method == 'POST':
        try:
            date_str = request.POST.get('date') or request.POST.get('attendance_date')
            class_id = request.POST.get('class_id')

            if not date_str or not class_id:
                return JsonResponse(
                    {'status': 'error', 'message': 'Date and class are required.'}, status=400
                )

            # Accept either a multi-value list (file 1) or a comma-separated string (file 2)
            detected_ids_raw = request.POST.getlist('detected_students[]')
            if not detected_ids_raw:
                csv_str = request.POST.get('detected_students', '')
                detected_ids_raw = [s.strip() for s in csv_str.split(',') if s.strip()]

            try:
                selected_date = date.fromisoformat(date_str)
                selected_class = get_object_or_404(Class, id=class_id)
            except ValueError:
                return JsonResponse(
                    {'status': 'error', 'message': 'Invalid date format.'}, status=400
                )

            detected_ids = {int(i) for i in detected_ids_raw if str(i).isdigit()}
            all_students = Student.objects.filter(student_class=selected_class, status=1)
            marked_present = 0

            for student in all_students:
                if student.id in detected_ids:
                    Attendance.objects.update_or_create(
                        student=student,
                        date=selected_date,
                        defaults={'status': 'present', 'remarks': 'Marked via Face Recognition'},
                    )
                    marked_present += 1
                else:
                    Attendance.objects.update_or_create(
                        student=student,
                        date=selected_date,
                        defaults={
                            'status': 'absent',
                            'remarks': 'Not detected by Face Recognition',
                        },
                    )
                    for parent in Parent.objects.filter(student=student).select_related('user'):
                        if parent.user.email:
                            send_mail(
                                subject=f'Attendance Alert: {student.name} was Absent - SRMS',
                                message=(
                                    f'Dear {parent.user.get_full_name()},\n\n'
                                    f'Your child {student.name} was marked ABSENT on {date_str} '
                                    '(via Face Recognition system).\n\n'
                                    'Please contact the school if you have any questions.\n\n'
                                    'Regards,\nSRMS School'
                                ),
                                from_email=None,
                                recipient_list=[parent.user.email],
                                fail_silently=True,
                            )

            return JsonResponse({
                'status': 'success',
                'message': f'Attendance saved. {marked_present} student(s) marked present.'
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return render(request, 'admin/face_attendance.html', {
        'classes': classes,
        'today': date.today(),
    })