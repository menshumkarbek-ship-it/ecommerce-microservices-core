from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('shop', '0005_userprofile_email_otp_userprofile_is_email_verified_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='passport_number',
            field=models.CharField(blank=True, max_length=9, null=True, unique=True),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='verification_method',
            field=models.CharField(default='email', max_length=10),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='password_change_otp',
            field=models.CharField(blank=True, max_length=6, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='password_change_otp_created_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]