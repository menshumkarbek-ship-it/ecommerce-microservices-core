from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('shop', '0006_email_only_verification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userprofile',
            name='passport_number',
            field=models.CharField(
                blank=True,
                help_text='Legacy field retained for existing accounts.',
                max_length=9,
                null=True,
                unique=True,
            ),
        ),
    ]