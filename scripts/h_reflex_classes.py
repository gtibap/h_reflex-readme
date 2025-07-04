class StimulationResponses:

    def __init__(self, df, num):
        self.df = df
        self.stim_number = num

    def myfunc(self):
        print(f"stimulation df: {self.df}")
        print(f"stim number: {self.stim_number}")

    def get_df(self):
        return self.df

    
