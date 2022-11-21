import datetime
from  thefuzz import fuzz
# date = datetime.datetime.strptime('12/10/2022','%d/%m/%Y').date()
# today = datetime.datetime.today().date()
# print(date, today)
bank_name = "RODRIGO RUIZ OSTOS"
desk_name = "RODRIGO IGNACIO RUIZ"
ratio = fuzz.token_sort_ratio(str(bank_name), str(desk_name))
print(ratio)