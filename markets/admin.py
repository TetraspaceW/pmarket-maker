from django.contrib import admin

# Register your models here.
from .models import Market, Option, BuyOrder, SellOrder,Transaction,Portfolio

admin.site.register(Option)
admin.site.register(BuyOrder)
admin.site.register(SellOrder)
admin.site.register(Transaction)
admin.site.register(Portfolio)

class OptionsInLine(admin.TabularInline):
    model = Option

class MarketAdmin(admin.ModelAdmin):
	inlines = [OptionsInLine]

admin.site.register(Market,MarketAdmin)