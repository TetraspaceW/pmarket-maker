import datetime

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import SellOrder, BuyOrder, Transaction, Portfolio

#ughhh so much repeated code in here
#also it might be better to add these to the save method instead of using signals
#ill fix this soon dont worry

@receiver(post_save, sender=SellOrder)
def executeSellOrder(sender,**kwargs):
	if kwargs['created']:
		sellOrder = kwargs['instance']
		option = sellOrder.option
		buyorderlist = option.buyorder_set.all().filter(maxPrice__gte = sellOrder.minPrice)

		for buyOrder in buyorderlist:
			transaction = Transaction()
			transaction.seller = sellOrder.creator
			transaction.buyer = buyOrder.creator
			transaction.price = buyOrder.maxPrice
			transaction.option = option
			transaction.creationdate = datetime.datetime.now()
			amount = min(buyOrder.maxNumber, sellOrder.maxNumber)
			transaction.amount = amount

			transaction.save()

			if buyOrder.maxNumber > amount:
				buyOrder.maxNumber -= amount
				buyOrder.save()
			else:
				buyOrder.delete()

			if sellOrder.maxNumber > amount:
				sellOrder.maxNumber -= amount
				sellOrder.save()
			else:
				sellOrder.delete()
				transaction.save()
				break;
	


	#what this should do:
	#search through the database for all buyorders from the same option
	#destroy X shares until there are no buyorders left, or the sellorder is empty
	#create transactions along the way

@receiver(post_save, sender=BuyOrder)
def executeBuyOrder(sender,**kwargs):
	if kwargs['created']:
		buyOrder = kwargs['instance']
		option = buyOrder.option
		sellOrderList = option.sellorder_set.all().filter(minPrice__lte = buyOrder.maxPrice)

		for sellOrder in sellOrderList:
			transaction = Transaction()
			transaction.seller = sellOrder.creator
			transaction.buyer = buyOrder.creator
			transaction.price = sellOrder.minPrice
			transaction.option = option
			transaction.creationdate = datetime.datetime.now()
			amount = min(buyOrder.maxNumber, sellOrder.maxNumber)
			transaction.amount = amount

			transaction.save()

			if sellOrder.maxNumber > amount:
				sellOrder.maxNumber -= amount
				sellOrder.save()
			else:
				sellOrder.delete()

			if buyOrder.maxNumber > amount:
				buyOrder.maxNumber -= amount
				buyOrder.save()
			else:
				buyOrder.delete()
				break;

@receiver(post_save,sender=Transaction)
def updatePortfolio(sender,**kwargs):
	if kwargs['created']:
		transaction = kwargs['instance']
		marketPortfolios = Portfolio.objects.all().filter(market=transaction.option.market)
		#there should only ever be one result from these queries
		sellerPortfolio = marketPortfolios.get(owner=transaction.seller)
		sellerPortfolio.balance += float(transaction.amount*transaction.price)
		sellerPortfolio.save()

		buyerPortfolio = marketPortfolios.get(owner=transaction.buyer)
		buyerPortfolio.balance -= float(transaction.amount*transaction.price)
		buyerPortfolio.save()
