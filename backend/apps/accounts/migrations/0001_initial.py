import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = [
        ('catalog', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name='AuthRateLimit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('key_hash', models.CharField(max_length=64, unique=True)),
                ('count', models.PositiveSmallIntegerField(default=0)),
                ('window_start', models.DateTimeField(default=django.utils.timezone.now)),
            ],
        ),
        migrations.CreateModel(
            name='OAuthFlow',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('state_hash', models.CharField(max_length=64, unique=True)),
                ('provider', models.CharField(max_length=12)),
                ('nonce', models.CharField(max_length=64)),
                ('expires_at', models.DateTimeField(db_index=True)),
            ],
        ),
        migrations.CreateModel(
            name='CustomerProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_key', models.EmailField(max_length=254, unique=True)),
                ('email_verified', models.BooleanField(default=False)),
                ('phone', models.CharField(blank=True, max_length=20)),
                ('city', models.CharField(blank=True, max_length=160)),
                ('address', models.CharField(blank=True, max_length=255)),
                ('np_branch', models.CharField(blank=True, max_length=255)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='customer_profile', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='EmailChallenge',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purpose', models.CharField(choices=[('verify', 'Verify email'), ('reset', 'Reset password')], max_length=8)),
                ('code_hash', models.CharField(max_length=128)),
                ('expires_at', models.DateTimeField()),
                ('sent_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='email_challenges', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='SavedCar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nickname', models.CharField(blank=True, max_length=80)),
                ('vin', models.CharField(blank=True, max_length=17)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('generation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='catalog.generation')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='saved_cars', to=settings.AUTH_USER_MODEL)),
            ],
            options={'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='SocialIdentity',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('provider', models.CharField(max_length=12)),
                ('subject', models.CharField(max_length=255)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='social_identities', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddConstraint(model_name='emailchallenge', constraint=models.UniqueConstraint(fields=('user', 'purpose'), name='unique_email_challenge')),
        migrations.AddConstraint(model_name='socialidentity', constraint=models.UniqueConstraint(fields=('provider', 'subject'), name='unique_social_subject')),
        migrations.AddConstraint(model_name='socialidentity', constraint=models.UniqueConstraint(fields=('user', 'provider'), name='unique_user_social_provider')),
    ]
