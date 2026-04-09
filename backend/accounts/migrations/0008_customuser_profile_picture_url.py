from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_signup_secret'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='profile_picture',
        ),
        migrations.AddField(
            model_name='customuser',
            name='profile_picture_url',
            field=models.URLField(blank=True, default='', help_text='Cloudinary URL for profile picture', max_length=500),
        ),
    ]
