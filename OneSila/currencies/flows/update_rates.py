from currencies.factories.update_rates import UpdateOfficialRateFactory, UpdateSingleRate


def update_rate_flow():
    f = UpdateOfficialRateFactory()
    f.run()


def update_single_rate_flow(currency):
    f = UpdateSingleRate(currency)
    f.run()
