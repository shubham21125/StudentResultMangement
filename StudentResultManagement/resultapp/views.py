from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from urllib3 import request
from .models import *
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from datetime import datetime, timedelta
from django.core.mail import send_mail  # ✅ EMAIL IMPORT

def index(request):
    notices = Notice.objects.all().order_by('-id')
    
    # Add statistics for homepage
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
    return render(request, 'notice_detail.html', locals())

def admin_login(request):
    if request.user.is_authenticated:
        return redirect('admin_dashboard')
    error = None
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_superuser:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            error = "Invalid credentials or not authorized."
    return render(request, 'admin_login.html', locals())

def admin_dashboard(request):
    if not request.user.is_authenticated:
        return redirect('admin-login')
    total_students = Student.objects.count()
    total_subjects = Subject.objects.count()
    total_classes = Class.objects.count()
    total_results = Result.objects.values('student').distinct().count()
    return render(request, 'admin_dashboard.html', locals())

def admin_logout(request):
    logout(request)
    return redirect('admin-login')

@login_required
def create_class(request):
    if request.method == 'POST':
        try:
            class_name = request.POST.get('classname')
            class_numeric = request.POST.get('classnamenumeric')
            section = request.POST.get('section')
            Class.objects.create(class_name=class_name, class_numeric=class_numeric, section=section)
            messages.success(request, "Class created successfully!")
            return redirect('create_class')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('create_class')
    return render(request, 'create_class.html')

@login_required
def manage_classes(request):
    classes = Class.objects.all()

    if request.GET.get('delete'):
        try:
            class_id = request.GET.get('delete')
            class_obj = get_object_or_404(Class, id=class_id)
            class_obj.delete()
            messages.success(request, "Class deleted successfully!")
            return redirect('manage_classes')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('manage_classes')
        
    return render(request, 'manage_classes.html', locals())

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
            return redirect('edit_class', class_id=class_id)
    
    return render(request, 'edit_class.html', locals())

@login_required
def create_subject(request):
    if request.method == 'POST':
        try:
            subject_name = request.POST.get('subjectname')
            subject_code = request.POST.get('subjectcode')
            Subject.objects.create(subject_name=subject_name, subject_code=subject_code)
            messages.success(request, "Subject created successfully!")
            return redirect('create_subject')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('create_subject')
    return render(request, 'create_subject.html')

@login_required
def manage_subject(request):
    subjects = Subject.objects.all()

    if request.GET.get('delete'):
        try:
            subject_id = request.GET.get('delete')
            subject_obj = get_object_or_404(Subject, id=subject_id)
            subject_obj.delete()
            messages.success(request, "Subject deleted successfully!")
            return redirect('manage_subject')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('manage_subject')

    return render(request, 'manage_subject.html', locals())

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
            return redirect('edit_subject', subject_id=subject_id)
    
    return render(request, 'edit_subject.html', locals())

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
            return redirect('add_subject_combination')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('create_subject')
    return render(request, 'add_subject_combination.html', locals())

@login_required
def manage_subject_combination(request):
    combinations = SubjectCombination.objects.all()
    aid = request.GET.get('aid')
    if request.GET.get('aid'):
        try:
            SubjectCombination.objects.filter(id=aid).update(status=1)
            messages.success(request, "Subject combination activated successfully!")
            return redirect('manage_subject_combination')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('manage_subject_combination')

    did = request.GET.get('did')
    if request.GET.get('did'):
        try:
            SubjectCombination.objects.filter(id=did).update(status=0)
            messages.success(request, "Subject combination deactivated successfully!")
            return redirect('manage_subject_combination')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('manage_subject_combination')

    return render(request, 'manage_subject_combination.html', locals())

@login_required
def add_student(request):
    classes = Class.objects.all()
    if request.method == 'POST':
        try:
            name = request.POST.get('fullname')
            roll_id = request.POST.get('rollid')
            email = request.POST.get('emailid')
            gender = request.POST.get('gender')
            dob = request.POST.get('dob')
            class_id = request.POST.get('class')
            student_class = Class.objects.get(id=class_id)
            Student.objects.create(
                name=name,
                roll_id=roll_id,
                email=email,
                gender=gender,
                dob=dob,
                student_class=student_class
            )
            messages.success(request, "Student info added successfully!")
            return redirect('add_student')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('add_student')
    return render(request, 'add_student.html', locals())

@login_required
def manage_students(request):
    students = Student.objects.all()
    return render(request, 'manage_students.html', locals())

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
    return render(request, 'edit_student.html', locals())

@login_required
def add_notice(request):
    if request.method == 'POST':
        try:
            title = request.POST.get('title')
            details = request.POST.get('details')
            Notice.objects.create(
                title=title,
                detail=details
            )

            # ✅ SEND EMAIL TO ALL STUDENTS AND PARENTS ABOUT NEW NOTICE
            all_student_emails = list(Student.objects.filter(status=1).values_list('email', flat=True))
            all_parent_emails = list(User.objects.filter(parent__isnull=False).values_list('email', flat=True))
            all_emails = list(set(all_student_emails + all_parent_emails))
            all_emails = [e for e in all_emails if e]  # remove empty emails

            if all_emails:
                send_mail(
                    subject=f'New Notice: {title} - SRMS',
                    message=f'Dear Student/Parent,\n\nA new notice has been posted:\n\nTitle: {title}\n\n{details}\n\nPlease visit the school portal for more details.\n\nRegards,\nSRMS College',
                    from_email='shubhamds21125@gmail.com',
                    recipient_list=all_emails,
                    fail_silently=True,
                )

            messages.success(request, "Notice added successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('add_notice')
    return render(request, 'add_notice.html', locals())

@login_required
def manage_notice(request):
    notices = Notice.objects.all()

    if request.GET.get('delete'):
        try:
            notice_id = request.GET.get('delete')
            notice_obj = get_object_or_404(Notice, id=notice_id)
            notice_obj.delete()
            messages.success(request, "Notice deleted successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('manage_notice')

    return render(request, 'manage_notice.html', locals())

@login_required
def add_result(request):
    classes = Class.objects.all()
    if request.method == 'POST':
        try:
            class_id = request.POST.get('class')
            student_id = request.POST.get('studentid')
            marks_data = {key.split('_')[1]: value for key, value in request.POST.items() if key.startswith('marks_')}
            for subject_id, marks in marks_data.items():
                Result.objects.create(student_id=student_id, student_class_id=class_id, subject_id=subject_id, marks=marks)

            # ✅ SEND EMAIL TO STUDENT WHEN RESULT IS ADDED
            student = Student.objects.get(id=student_id)
            if student.email:
                send_mail(
                    subject='Your Result Has Been Added - SRMS',
                    message=f'Dear {student.name},\n\nYour result has been added successfully by the school.\n\nPlease visit the school portal to check your full result.\n\nRoll ID: {student.roll_id}\nClass: {student.student_class}\n\nRegards,\nSRMS College',
                    from_email='shubhamds21125@gmail.com',
                    recipient_list=[student.email],
                    fail_silently=True,
                )

            # ✅ ALSO NOTIFY PARENTS OF THIS STUDENT
            parents = Parent.objects.filter(student=student)
            for parent in parents:
                if parent.user.email:
                    send_mail(
                        subject=f'Result Added for {student.name} - SRMS',
                        message=f'Dear {parent.user.get_full_name()},\n\nThe result for your child {student.name} has been added.\n\nPlease login to the parent portal to view the full result.\n\nRegards,\nSRMS College',
                        from_email='shubhamds21125@gmail.com',
                        recipient_list=[parent.user.email],
                        fail_silently=True,
                    )

            messages.success(request, "Result info added successfully!")
            return redirect('add_result')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
            return redirect('add_result')
    return render(request, 'add_result.html', locals())

from django.http import JsonResponse
def get_students_subjects(request):
    class_id = request.GET.get('class_id')

    if class_id:
        students = list(Student.objects.filter(student_class_id=class_id).values('id', 'name', 'roll_id'))
        subject_combinations = SubjectCombination.objects.filter(student_class_id=class_id, status=1).select_related('subject')
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
            result_obj.marks = marks_list[i]
            result_obj.save()

        # ✅ SEND EMAIL TO STUDENT WHEN RESULT IS UPDATED
        if student.email:
            send_mail(
                subject='Your Result Has Been Updated - SRMS',
                message=f'Dear {student.name},\n\nYour result has been updated by the school.\n\nPlease visit the school portal to check your updated result.\n\nRoll ID: {student.roll_id}\nClass: {student.student_class}\n\nRegards,\nSRMS College',
                from_email='shubhamds21125@gmail.com',
                recipient_list=[student.email],
                fail_silently=True,
            )

        # ✅ ALSO NOTIFY PARENTS WHEN RESULT IS UPDATED
        parents = Parent.objects.filter(student=student)
        for parent in parents:
            if parent.user.email:
                send_mail(
                    subject=f'Result Updated for {student.name} - SRMS',
                    message=f'Dear {parent.user.get_full_name()},\n\nThe result for your child {student.name} has been updated.\n\nPlease login to the parent portal to view the updated result.\n\nRegards,\nSRMS College',
                    from_email='shubhamds21125@gmail.com',
                    recipient_list=[parent.user.email],
                    fail_silently=True,
                )

        messages.success(request, "Results updated successfully!")
        return redirect('manage_result')
    return render(request, 'edit_result.html', locals())

from django.contrib.auth import update_session_auth_hash
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

    return render(request, 'change_password.html', locals())

def search_result(request):
    classes = Class.objects.all()
    return render(request, 'search_result.html', locals())

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

def check_result(request):
    if request.method == 'POST':
        rollid = request.POST['rollid']
        class_id = request.POST['class']

        try:
            student = Student.objects.get(roll_id=rollid, student_class_id=class_id)
            results = Result.objects.filter(student=student)

            if not results.exists():
                messages.error(request, "No result found for the provided Roll ID and Class.")
                return redirect('search_result')

            total_marks = sum([r.marks for r in results])
            subject_count = results.count()
            max_total = subject_count * 100
            percentage = (total_marks / max_total) * 100 if max_total > 0 else 0
            percentage = round(percentage, 2)

            failed_subjects = []
            passed_subjects = []

            for r in results:
                if r.marks < 35:
                    failed_subjects.append(r)
                else:
                    passed_subjects.append(r)

            is_failed = len(failed_subjects) > 0
            grade = get_grade(percentage, is_failed)

            context = {
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
            }

            return render(request, 'result_page.html', context)

        except Student.DoesNotExist:
            messages.error(request, "No result found for the provided Roll ID and Class.")
            return redirect('search_result')
        except Exception as e:
            messages.error(request, "Something went wrong. Please try again.")
            return redirect('search_result')

# ==================== PARENT PORTAL VIEWS ====================

def parent_login(request):
    if request.user.is_authenticated:
        try:
            parent = Parent.objects.get(user=request.user)
            return redirect('parent_dashboard')
        except Parent.DoesNotExist:
            pass

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            try:
                parent = Parent.objects.get(user=user)
                login(request, user)
                messages.success(request, f'Welcome {user.get_full_name()}!')
                return redirect('parent_dashboard')
            except Parent.DoesNotExist:
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
        total_days = Attendance.objects.filter(
            student=student,
            date__gte=thirty_days_ago
        ).count()

        present_days = Attendance.objects.filter(
            student=student,
            date__gte=thirty_days_ago,
            status='present'
        ).count()

        attendance_percentage = (present_days / total_days * 100) if total_days > 0 else 0

        recent_results = Result.objects.filter(student=student).order_by('-posting_date')[:5]
        latest_progress = ProgressReport.objects.filter(student=student).order_by('-created_at').first()
        avg_marks = Result.objects.filter(student=student).aggregate(Avg('marks'))['marks__avg'] or 0

        all_results = Result.objects.filter(student=student)
        failed_subjects = [r for r in all_results if r.marks < 35]
        is_failed = len(failed_subjects) > 0

        context = {
            'parent': parent,
            'student': student,
            'total_days': total_days,
            'present_days': present_days,
            'attendance_percentage': round(attendance_percentage, 2),
            'recent_results': recent_results,
            'latest_progress': latest_progress,
            'avg_marks': round(avg_marks, 2),
            'is_failed': is_failed,
            'failed_subjects': failed_subjects,
        }

        return render(request, 'parent/dashboard.html', context)
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('parent_login')

@login_required(login_url='parent_login')
def parent_view_attendance(request):
    try:
        parent = Parent.objects.get(user=request.user)
        student = parent.student

        selected_month = request.GET.get('month')
        selected_year = request.GET.get('year', datetime.now().year)

        if selected_month:
            attendance_records = Attendance.objects.filter(
                student=student,
                date__month=selected_month,
                date__year=selected_year
            ).order_by('-date')
        else:
            attendance_records = Attendance.objects.filter(
                student=student,
                date__month=datetime.now().month,
                date__year=datetime.now().year
            ).order_by('-date')

        total_records = attendance_records.count()
        present_count = attendance_records.filter(status='present').count()
        absent_count = attendance_records.filter(status='absent').count()
        late_count = attendance_records.filter(status='late').count()

        context = {
            'student': student,
            'attendance_records': attendance_records,
            'total_records': total_records,
            'present_count': present_count,
            'absent_count': absent_count,
            'late_count': late_count,
            'selected_month': selected_month,
            'selected_year': selected_year,
        }

        return render(request, 'parent/attendance.html', context)
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('parent_login')

@login_required(login_url='parent_login')
def parent_view_results(request):
    try:
        parent = Parent.objects.get(user=request.user)
        student = parent.student

        results = Result.objects.filter(student=student).select_related('subject').order_by('-posting_date')

        failed_subjects = []
        passed_subjects = []

        for r in results:
            if r.marks < 35:
                failed_subjects.append(r)
            else:
                passed_subjects.append(r)

        is_failed = len(failed_subjects) > 0

        if results.exists():
            total_marks = sum(r.marks for r in results)
            max_marks = len(results) * 100
            percentage = (total_marks / max_marks * 100) if max_marks > 0 else 0
            avg_marks = results.aggregate(Avg('marks'))['marks__avg']
            grade = get_grade(round(percentage, 2), is_failed)
        else:
            total_marks = 0
            max_marks = 0
            percentage = 0
            avg_marks = 0
            grade = 'N/A'

        context = {
            'student': student,
            'results': results,
            'total_marks': total_marks,
            'max_marks': max_marks,
            'percentage': round(percentage, 2),
            'avg_marks': round(avg_marks, 2) if avg_marks else 0,
            'failed_subjects': failed_subjects,
            'passed_subjects': passed_subjects,
            'is_failed': is_failed,
            'grade': grade,
        }

        return render(request, 'parent/results.html', context)
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('parent_login')

@login_required(login_url='parent_login')
def parent_view_progress(request):
    try:
        parent = Parent.objects.get(user=request.user)
        student = parent.student

        progress_reports = ProgressReport.objects.filter(
            student=student
        ).order_by('-created_at')

        context = {
            'student': student,
            'progress_reports': progress_reports,
        }

        return render(request, 'parent/progress.html', context)
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('parent_login')

@login_required(login_url='parent_login')
def parent_profile(request):
    try:
        parent = Parent.objects.get(user=request.user)
        student = parent.student

        context = {
            'parent': parent,
            'student': student,
        }

        return render(request, 'parent/profile.html', context)
    except Parent.DoesNotExist:
        messages.error(request, 'Parent profile not found.')
        return redirect('parent_login')

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
            from django.contrib.auth.models import User
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )

            student = Student.objects.get(id=student_id)
            Parent.objects.create(
                user=user,
                phone=phone,
                address=address,
                student=student,
                relationship=relationship
            )

            # ✅ SEND EMAIL TO PARENT WITH LOGIN DETAILS
            if email:
                send_mail(
                    subject='Your Parent Account Has Been Created - SRMS',
                    message=f'Dear {first_name} {last_name},\n\nYour parent account has been created successfully!\n\nLogin Details:\nUsername: {username}\nPassword: {password}\nLogin URL: http://127.0.0.1:8000/parent-login/\n\nYou can now track the following for {student.name}:\n- Results & Marks\n- Attendance\n- Progress Reports\n\nRegards,\nSRMS College',
                    from_email='shubhamds21125@gmail.com',
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
    parents = Parent.objects.all().select_related('user', 'student')

    if request.GET.get('delete'):
        try:
            parent_id = request.GET.get('delete')
            parent_obj = get_object_or_404(Parent, id=parent_id)
            user = parent_obj.user
            parent_obj.delete()
            user.delete()
            messages.success(request, "Parent account deleted successfully!")
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")
        return redirect('manage_parents')

    return render(request, 'admin/manage_parents.html', {'parents': parents})

@login_required
def add_attendance(request):
    classes = Class.objects.all()

    if request.method == 'POST':
        try:
            class_id = request.POST.get('class')
            date = request.POST.get('date')
            students = Student.objects.filter(student_class_id=class_id)

            for student in students:
                status = request.POST.get(f'status_{student.id}')
                remarks = request.POST.get(f'remarks_{student.id}', '')

                Attendance.objects.update_or_create(
                    student=student,
                    date=date,
                    defaults={'status': status, 'remarks': remarks}
                )

                # ✅ SEND EMAIL TO PARENT IF STUDENT IS ABSENT
                if status == 'absent':
                    parents = Parent.objects.filter(student=student)
                    for parent in parents:
                        if parent.user.email:
                            send_mail(
                                subject=f'Attendance Alert: {student.name} was Absent - SRMS',
                                message=f'Dear {parent.user.get_full_name()},\n\nThis is to inform you that your child {student.name} was marked ABSENT on {date}.\n\nRemarks: {remarks if remarks else "No remarks"}\n\nPlease contact the school if you have any questions.\n\nRegards,\nSRMS School',
                                from_email='shubhamds21125@gmail.com',
                                recipient_list=[parent.user.email],
                                fail_silently=True,
                            )

            messages.success(request, "Attendance recorded successfully!")
            return redirect('add_attendance')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")

    return render(request, 'admin/add_attendance.html', {'classes': classes})

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
                areas_of_improvement=areas_of_improvement
            )

            # ✅ SEND EMAIL TO PARENTS WHEN PROGRESS REPORT IS ADDED
            student = Student.objects.get(id=student_id)
            parents = Parent.objects.filter(student=student)
            for parent in parents:
                if parent.user.email:
                    send_mail(
                        subject=f'Progress Report Added - {term} - SRMS',
                        message=f'Dear {parent.user.get_full_name()},\n\nA new progress report has been added for {student.name}.\n\nReport Details:\nTerm: {term}\nGrade: {grade}\nOverall Percentage: {overall_percentage}%\nTeacher Remarks: {teacher_remarks}\nStrengths: {strengths if strengths else "N/A"}\nAreas of Improvement: {areas_of_improvement if areas_of_improvement else "N/A"}\n\nPlease login to the parent portal for more details.\n\nRegards,\nSRMS College',
                        from_email='shubhamds21125@gmail.com',
                        recipient_list=[parent.user.email],
                        fail_silently=True,
                    )

            messages.success(request, "Progress report added successfully!")
            return redirect('add_progress_report')
        except Exception as e:
            messages.error(request, f"Something went wrong: {str(e)}")

    return render(request, 'admin/add_progress_report.html', {'students': students})

from django.http import JsonResponse

def get_student_percentage(request):
    student_id = request.GET.get('student_id')
    
    if not student_id:
        return JsonResponse({'percentage': None, 'grade': 'N/A'})
    
    try:
        student = Student.objects.get(id=student_id)
        results = Result.objects.filter(student=student)
        
        if not results.exists():
            return JsonResponse({'percentage': None, 'grade': 'N/A'})
        
        total_marks = sum([r.marks for r in results])
        subject_count = results.count()
        max_total = subject_count * 100
        percentage = (total_marks / max_total) * 100 if max_total > 0 else 0
        percentage = round(percentage, 2)
        
        failed_subjects = [r for r in results if r.marks < 35]
        is_failed = len(failed_subjects) > 0
        grade = get_grade(percentage, is_failed)
        
        return JsonResponse({
            'percentage': percentage,
            'grade': grade
        })
        
    except Student.DoesNotExist:
        return JsonResponse({'percentage': None, 'grade': 'N/A'})
    except Exception as e:
        return JsonResponse({'percentage': None, 'grade': 'N/A', 'error': str(e)})