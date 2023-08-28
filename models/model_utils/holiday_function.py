import pandas as pd
from datetime import datetime
import pytz


class SouthAfricanHolidays:

    def __init__(self, year):
        self.year = year
        self.sa_holidays = pd.DataFrame(columns=[])
        
    def  create_holidays_df(self):
    
      holidays = pd.DataFrame({
            'holiday': 'South African holidays',
            'ds': pd.date_range(start=f'{self.year}-01-01', end=f'{self.year}-12-31', freq='D')
    })
            
        # Add New Year's Day
      holidays.loc[(holidays.ds.dt.month == 1) & (holidays.ds.dt.day == 1), 'holiday'] = "New Year's Day"
        
        # Add Human Rights Day
      holidays.loc[(holidays.ds.dt.month == 3) & (holidays.ds.dt.day == 21), 'holiday'] = "Human Rights Day"

         # Add Good Friday 
      easter = holidays.ds.dt.date + pd.offsets.Easter()
      good_friday = easter - pd.Timedelta(days=2)
      holidays.loc[holidays.ds == good_friday, 'holiday'] = "Good Friday"

        # Add Family Day
      family_day = easter + pd.Timedelta(days=1)
      holidays.loc[holidays.ds == family_day, 'holiday'] = "Family Day"

        # Add Freedom Day
      holidays.loc[(holidays.ds.dt.month == 4) & (holidays.ds.dt.day == 27), 'holiday'] = "Freedom Day"

        # Add Workers' Day
      holidays.loc[(holidays.ds.dt.month == 5) & (holidays.ds.dt.day == 1), 'holiday'] = "Workers' Day"

        # Add Youth Day
      holidays.loc[(holidays.ds.dt.month == 6) & (holidays.ds.dt.day == 16), 'holiday'] = "Youth Day"

        # Add National Women's Day
      holidays.loc[(holidays.ds.dt.month == 8) & (holidays.ds.dt.day == 9), 'holiday'] = "National Women's Day"

        # Add Heritage Day
      holidays.loc[(holidays.ds.dt.month == 9) & (holidays.ds.dt.day == 24), 'holiday'] = "Heritage Day"

        # Add Day of Reconciliation
      holidays.loc[(holidays.ds.dt.month == 12) & (holidays.ds.dt.day == 16), 'holiday'] = "Day of Reconciliation"

        # Add Christmas Day
      holidays.loc[(holidays.ds.dt.month == 12) & (holidays.ds.dt.day == 25), 'holiday'] = "Christmas Day"

        # Add Day of Goodwill
      holidays.loc[(holidays.ds.dt.month == 12) & (holidays.ds.dt.day == 26), 'holiday'] = "Day of Goodwill"

        # Set index to the holiday dates
      holidays.set_index('ds', inplace=True)
        
      self.sa_holidays = pd.concat([holidays, self.sa_holidays], axis=0)
      self.sa_holidays = self.sa_holidays[self.sa_holidays['holiday'] != 'South African holidays']
      
      return self.sa_holidays
    
    def get_sa_holiday(self, month, day):
        try:
            return self.sa_holidays[
                (self.sa_holidays.index.month == month) & (self.sa_holidays.index.day == day)
            ]['holiday'].values[0]
        except Exception as e:
            return 'Not Holiday'

