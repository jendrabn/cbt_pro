from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.accounts.models import UserProfile
from apps.notifications.models import SystemSetting
from apps.subjects.models import Subject

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed the database with initial data'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Starting database seeding...'))
        
        # Create admin user
        self.create_admin_user()

        # Create teacher and student users
        self.create_teacher_users()
        self.create_student_users()
        
        # Create sample subjects
        self.create_subjects()
        
        # Create default system settings
        self.create_system_settings()
        
        self.stdout.write(self.style.SUCCESS('Database seeding completed!'))
    
    def create_admin_user(self):
        """Create default admin user"""
        if not User.objects.filter(username='admin').exists():
            admin = User.objects.create_superuser(
                username='admin',
                email='admin@cbt.com',
                password='admin123',  # Change in production!
                first_name='System',
                last_name='Administrator',
                role='admin'
            )
            self.stdout.write(self.style.SUCCESS(f'Created admin user: {admin.username}'))
        else:
            self.stdout.write(self.style.WARNING('Admin user already exists'))
    
    def create_subjects(self):
        """Create sample subjects"""
        subjects_data = [
            {'name': 'Mathematics', 'code': 'MATH', 'description': 'Mathematics and Calculus'},
            {'name': 'Physics', 'code': 'PHY', 'description': 'Physics and Natural Sciences'},
            {'name': 'Chemistry', 'code': 'CHEM', 'description': 'Chemistry and Lab Sciences'},
            {'name': 'Biology', 'code': 'BIO', 'description': 'Biology and Life Sciences'},
            {'name': 'English', 'code': 'ENG', 'description': 'English Language and Literature'},
            {'name': 'Computer Science', 'code': 'CS', 'description': 'Programming and Computer Science'},
        ]
        
        for subject_data in subjects_data:
            subject, created = Subject.objects.get_or_create(
                name=subject_data['name'],
                defaults={
                    'code': subject_data['code'],
                    'description': subject_data['description'],
                    'is_active': True
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created subject: {subject.name}'))
            else:
                updated = False
                for field in ("code", "description", "is_active"):
                    expected_value = subject_data[field]
                    if getattr(subject, field) != expected_value:
                        setattr(subject, field, expected_value)
                        updated = True
                if updated:
                    subject.save(update_fields=["code", "description", "is_active", "updated_at"])
                    self.stdout.write(self.style.SUCCESS(f'Updated subject: {subject.name}'))
                    continue
                self.stdout.write(self.style.WARNING(f'Subject already exists: {subject.name}'))

    def create_teacher_users(self):
        """Create default teacher users"""
        teachers_data = [
            {
                'username': 'guru.matematika',
                'email': 'guru.matematika@cbt.com',
                'password': 'guru123',
                'first_name': 'Budi',
                'last_name': 'Santoso',
                'teacher_id': 'NIP-1001',
                'subject_specialization': 'Matematika',
            },
            {
                'username': 'guru.bahasa',
                'email': 'guru.bahasa@cbt.com',
                'password': 'guru123',
                'first_name': 'Siti',
                'last_name': 'Rahma',
                'teacher_id': 'NIP-1002',
                'subject_specialization': 'Bahasa Inggris',
            },
        ]

        for teacher_data in teachers_data:
            defaults = {
                'email': teacher_data['email'],
                'first_name': teacher_data['first_name'],
                'last_name': teacher_data['last_name'],
                'role': 'teacher',
                'is_active': True,
            }
            user, created = User.objects.get_or_create(
                username=teacher_data['username'],
                defaults=defaults,
            )

            if created:
                user.set_password(teacher_data['password'])
                user.save(update_fields=['password'])
                self.stdout.write(self.style.SUCCESS(f'Created teacher user: {user.username}'))
            else:
                updated = False
                for field, value in defaults.items():
                    if getattr(user, field) != value:
                        setattr(user, field, value)
                        updated = True
                if getattr(user, 'is_deleted', False):
                    user.is_deleted = False
                    updated = True
                if updated:
                    user.save()
                self.stdout.write(self.style.WARNING(f'Teacher user already exists: {user.username}'))

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'teacher_id': teacher_data['teacher_id'],
                    'subject_specialization': teacher_data['subject_specialization'],
                },
            )

    def create_student_users(self):
        """Create default student users"""
        students_data = [
            {
                'username': 'siswa.andi',
                'email': 'siswa.andi@cbt.com',
                'password': 'siswa123',
                'first_name': 'Andi',
                'last_name': 'Pratama',
                'student_id': 'NIS-2001',
                'class_grade': 'XII IPA 1',
            },
            {
                'username': 'siswa.dewi',
                'email': 'siswa.dewi@cbt.com',
                'password': 'siswa123',
                'first_name': 'Dewi',
                'last_name': 'Lestari',
                'student_id': 'NIS-2002',
                'class_grade': 'XII IPA 2',
            },
            {
                'username': 'siswa.rizky',
                'email': 'siswa.rizky@cbt.com',
                'password': 'siswa123',
                'first_name': 'Rizky',
                'last_name': 'Saputra',
                'student_id': 'NIS-2003',
                'class_grade': 'XI IPS 1',
            },
        ]

        for student_data in students_data:
            defaults = {
                'email': student_data['email'],
                'first_name': student_data['first_name'],
                'last_name': student_data['last_name'],
                'role': 'student',
                'is_active': True,
            }
            user, created = User.objects.get_or_create(
                username=student_data['username'],
                defaults=defaults,
            )

            if created:
                user.set_password(student_data['password'])
                user.save(update_fields=['password'])
                self.stdout.write(self.style.SUCCESS(f'Created student user: {user.username}'))
            else:
                updated = False
                for field, value in defaults.items():
                    if getattr(user, field) != value:
                        setattr(user, field, value)
                        updated = True
                if getattr(user, 'is_deleted', False):
                    user.is_deleted = False
                    updated = True
                if updated:
                    user.save()
                self.stdout.write(self.style.WARNING(f'Student user already exists: {user.username}'))

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    'student_id': student_data['student_id'],
                    'class_grade': student_data['class_grade'],
                },
            )
    
    def create_system_settings(self):
        """Create default system settings"""
        settings_data = [
            {
                'setting_key': 'institution_name',
                'setting_value': '',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Nama sekolah/lembaga',
                'is_public': True
            },
            {
                'setting_key': 'institution_type',
                'setting_value': '',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Jenis lembaga (SMA/SMK/MA/Universitas)',
                'is_public': True
            },
            {
                'setting_key': 'institution_address',
                'setting_value': '',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Alamat lembaga',
                'is_public': False
            },
            {
                'setting_key': 'institution_phone',
                'setting_value': '',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Nomor telepon/WA lembaga',
                'is_public': False
            },
            {
                'setting_key': 'institution_email',
                'setting_value': '',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Email resmi lembaga',
                'is_public': False
            },
            {
                'setting_key': 'institution_website',
                'setting_value': '',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Website resmi lembaga',
                'is_public': True
            },
            {
                'setting_key': 'institution_logo_url',
                'setting_value': '',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Path logo utama',
                'is_public': True
            },
            {
                'setting_key': 'institution_logo_dark_url',
                'setting_value': '',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Path logo dark',
                'is_public': True
            },
            {
                'setting_key': 'institution_favicon_url',
                'setting_value': '',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Path favicon',
                'is_public': True
            },
            {
                'setting_key': 'login_page_headline',
                'setting_value': '',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Headline login page',
                'is_public': True
            },
            {
                'setting_key': 'login_page_subheadline',
                'setting_value': '',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Subheadline login page',
                'is_public': True
            },
            {
                'setting_key': 'login_page_background_url',
                'setting_value': '',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Path background login',
                'is_public': True
            },
            {
                'setting_key': 'primary_color',
                'setting_value': '#0d6efd',
                'setting_type': 'string',
                'category': 'branding',
                'description': 'Warna utama UI',
                'is_public': True
            },
            {
                'setting_key': 'landing_page_enabled',
                'setting_value': 'true',
                'setting_type': 'boolean',
                'category': 'general',
                'description': 'Aktifkan landing page di URL root',
                'is_public': True
            },
            {
                'setting_key': 'default_exam_duration',
                'setting_value': '120',
                'setting_type': 'number',
                'category': 'exam_defaults',
                'description': 'Default exam duration in minutes',
                'is_public': False
            },
            {
                'setting_key': 'default_passing_score',
                'setting_value': '60',
                'setting_type': 'number',
                'category': 'exam_defaults',
                'description': 'Default passing score percentage',
                'is_public': False
            },
            {
                'setting_key': 'max_login_attempts',
                'setting_value': '5',
                'setting_type': 'number',
                'category': 'security',
                'description': 'Maximum login attempts before lockout',
                'is_public': False
            },
            {
                'setting_key': 'session_timeout_minutes',
                'setting_value': '120',
                'setting_type': 'number',
                'category': 'security',
                'description': 'User session timeout in minutes',
                'is_public': False
            },
            {
                'setting_key': 'certificates_enabled',
                'setting_value': 'true',
                'setting_type': 'boolean',
                'category': 'certificates',
                'description': 'Master switch fitur sertifikat',
                'is_public': False
            },
            {
                'setting_key': 'certificate_number_prefix',
                'setting_value': 'CERT',
                'setting_type': 'string',
                'category': 'certificates',
                'description': 'Prefix nomor sertifikat',
                'is_public': False
            },
            {
                'setting_key': 'certificate_pdf_dpi',
                'setting_value': '150',
                'setting_type': 'number',
                'category': 'certificates',
                'description': 'Resolusi render PDF sertifikat',
                'is_public': False
            },
            {
                'setting_key': 'certificate_storage_path',
                'setting_value': 'certificates/',
                'setting_type': 'string',
                'category': 'certificates',
                'description': 'Direktori penyimpanan sertifikat',
                'is_public': False
            },
            {
                'setting_key': 'certificate_email_enabled',
                'setting_value': 'false',
                'setting_type': 'boolean',
                'category': 'certificates',
                'description': 'Kirim email saat sertifikat siap',
                'is_public': False
            },
            {
                'setting_key': 'certificate_verify_public',
                'setting_value': 'true',
                'setting_type': 'boolean',
                'category': 'certificates',
                'description': 'Verifikasi sertifikat publik',
                'is_public': True
            },
        ]
        
        for setting_data in settings_data:
            setting, created = SystemSetting.objects.get_or_create(
                setting_key=setting_data['setting_key'],
                defaults=setting_data
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created setting: {setting.setting_key}'))
            else:
                self.stdout.write(self.style.WARNING(f'Setting already exists: {setting.setting_key}'))
