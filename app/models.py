from django.db import models
from django.contrib.auth.models import User

class performance_center(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)

    class Meta:
        managed = False
        db_table = 'performance_center'


class performance_lab(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=100)
    FK_performance_center_id = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'performance_lab'

class PARAM_sections(models.Model):
    sectionid = models.IntegerField(primary_key=True)
    sectionname = models.CharField(max_length=256)
    displayName = models.CharField(max_length=512)

    class Meta:
        managed = False
        db_table = 'PARAM_sections'

class PARAM_options(models.Model):
    optionid = models.IntegerField(primary_key=True)
    optionname = models.CharField(max_length=256)
    ordering = models.IntegerField()
    displayName = models.CharField(max_length=512)
    toolTip = models.CharField(max_length=2048)
    type = models.CharField(max_length=30)
    maxlength = models.IntegerField()
    min = models.IntegerField()
    max = models.DecimalField(max_digits=11, decimal_places=10)
    default_value = models.CharField(max_length=256)
    selectionIncrements = models.IntegerField()
    visible = models.IntegerField()
    method = models.IntegerField()
    displayHTML = models.CharField(max_length=128)
    FK_sectionid = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'PARAM_options'


class PARAM_stored_values(models.Model):
    FK_parameterid = models.IntegerField()
    FK_optionid = models.IntegerField()
    finalvalue = models.CharField(max_length=512)

    class Meta:
        managed = False
        db_table = 'PARAM_stored_values'


class PARAM_stored(models.Model):
    id = models.AutoField(primary_key=True)
    createdate = models.DateTimeField(auto_now_add=True)
    description = models.CharField(max_length=512)
    identifier = models.CharField(max_length=250)
    active = models.IntegerField(default=1)
    doi_pub = models.CharField(max_length=50)
    objectid_uuid = models.CharField(max_length=50)
    FK_session_id = models.CharField(max_length=100)
    FK_exp_type = models.IntegerField()
    FK_userid = models.IntegerField()
    FK_performance_lab_id = models.IntegerField()
    publication_name = models.CharField(max_length=1024)

    class Meta:
        managed = False
        db_table = 'PARAM_stored'


class PARAM_methods(models.Model):
    methodid = models.AutoField(primary_key=True)
    methodname = models.CharField(max_length=256)
    tooltip = models.CharField(max_length=2048)
    methodhelp = models.CharField(max_length=2048)
    FK_section = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'PARAM_methods'
