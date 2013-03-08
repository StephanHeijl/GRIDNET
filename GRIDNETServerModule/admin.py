from django.contrib import admin
from GRIDNET.models import *

class JobAdmin(admin.ModelAdmin):
	list_display = ('id','owner','created_on','started_on','status')

class GridAdmin(admin.ModelAdmin):
	list_display = ('name', 'location','IP','last_update')	
	
class NodeAdmin(admin.ModelAdmin):
	list_display = ('name','connected', 'grid')
	
class SlotAdmin(admin.ModelAdmin):
	list_display = ('state','node')
	
admin.site.register(SubscribedUser)
admin.site.register(Subscription)
admin.site.register(Task)
admin.site.register(Action)
admin.site.register(Job, JobAdmin)
admin.site.register(TileScreen)
admin.site.register(Tile)
admin.site.register(Cont)
admin.site.register(Grid, GridAdmin)
admin.site.register(Node, NodeAdmin)
admin.site.register(Slot, SlotAdmin)
admin.site.register(NodeTask)
admin.site.register(Application)
