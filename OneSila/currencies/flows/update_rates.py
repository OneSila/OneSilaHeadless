from factories.update_rates import UpdateOfficialRateFactory, FollowerRateFactory


class UpdateOfficialRateFlow:
    def __init__(self):
        self.factory = UpdateOfficialRateFactory()

    def flow(self):
        self.factory.run()


class UpdateFollowerRateFlow:
    def __init__(self, currency):
        self.factory = FollowerRateFactory(currency)

    def flow(self):
        self.factory.run()
