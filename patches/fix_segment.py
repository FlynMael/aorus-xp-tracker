path = "scripts/notify_bosses.py"
s = open(path, encoding="utf-8").read()
old = '"included_segments": ["Subscribed Users"],'
new = '"included_segments": ["Total Subscriptions"],'
assert s.count(old) == 1
s = s.replace(old, new)
open(path, "w", encoding="utf-8").write(s)
print("ok")
