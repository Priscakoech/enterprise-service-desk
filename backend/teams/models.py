from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100)
    abbreviation = models.CharField(max_length=10, blank=True, help_text='Short code e.g. IT, HR, FIN. Auto-generated if blank.')
    description = models.TextField(blank=True, null=True)
    manager = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        limit_choices_to={'role': 'manager'},
    )

    def save(self, *args, **kwargs):
        if not self.abbreviation:
            # Auto-generate: take first letter of each word, uppercase
            words = self.name.split()
            if len(words) == 1:
                self.abbreviation = self.name[:3].upper()
            else:
                self.abbreviation = ''.join(w[0] for w in words).upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Team(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        related_name='teams',
        null=True,
        blank=True,
    )
    members = models.ManyToManyField(
        'accounts.CustomUser',
        related_name='team_memberships',
        blank=True,
    )

    def __str__(self):
        return self.name


class BusinessUnit(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class SupportGroup(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name
