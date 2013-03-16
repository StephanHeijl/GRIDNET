from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
#from GRIDNET import admin as adm

urlpatterns = patterns('',
    # Example:
    #(r'^GRIDNET/', include('GRIDNET.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
	(r'^$', 'GRIDNET.views.index'),
	(r'^index.htm$', 'GRIDNET.views.index'),
	(r'^tour$', 'GRIDNET.views.tour'),
    (r'^addJobWizard.action$', 'GRIDNET.views.addJobWizardDo'),
	(r'^addJobManual.action$', 'GRIDNET.views.addJobManualDo'),
    (r'^changePassword.action$', 'GRIDNET.views.changePasswordDo'),
    (r'^changeNodeTasks.action$', 'GRIDNET.views.changeNodeTaskDo'),
    (r'^tasksDropdown.get$', 'GRIDNET.views.getDropdownTasks'),
    (r'^gridsDropdown.get$', 'GRIDNET.views.getDropdownGrids'),
    (r'^nodesDropdown.get$', 'GRIDNET.views.getDropdownNodes'),
    (r'^imageB64.get$', 'GRIDNET.views.convertToB64'),
    (r'^jobs.get$', 'GRIDNET.views.getJobs'),
    (r'^grids.get$', 'GRIDNET.views.getGrids'),
    (r'^tasks.get$', 'GRIDNET.views.getTasks'),
    (r'^logout.htm$', 'GRIDNET.views.logout_page'),
    (r'^/?files/(?P<file>.+)$', 'GRIDNET.views.files'),
    (r'^screen.htm$', 'GRIDNET.views.screen'),
    (r'^cont.htm$', 'GRIDNET.views.cont'),
    (r'^jobs/(?P<type>.+)$', 'GRIDNET.views.jobs'),
    (r'^reportState$', 'GRIDNET.views.currentState'),
    (r'^/?results/(?P<job>.+)$', 'GRIDNET.views.results'),
    (r'^admin/', include(admin.site.urls)),
)