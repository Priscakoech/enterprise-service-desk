from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('servicedesk', '0008_add_is_system_default_to_slapolicy'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attachment',
            name='file',
        ),
        migrations.AddField(
            model_name='attachment',
            name='file_url',
            field=models.URLField(default='', help_text='Cloudinary secure URL', max_length=500),
            preserve_default=False,
        ),
    ]
