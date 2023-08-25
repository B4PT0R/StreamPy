from googleapiclient.discovery import build

def get_google_search(api_key,cse_id):
    def google_search(query, num=5, type='web'):
        service = build("customsearch", "v1", developerKey=api_key)
        ns = num // 10
        r = num % 10
        results = []
        if not ns == 0:
            for i in range(ns):
                args_dict = {
                    'cx': cse_id,
                    'q': query,
                    'num': 10,
                    'start': 1 + i * 10
                }
                if type == 'image':
                    args_dict['searchType'] = 'image'
                res = service.cse().list(**args_dict).execute()
                for item in res['items']:
                    results.append({
                        'title': item['title'],
                        'description': item['snippet'] if item.get('snippet') else "",
                        'url': item['link']
                    })
        if not r == 0:
            args_dict = {
                'cx': cse_id,
                'q': query,
                'num': r,
                'start': 1 + ns * 10
            }
            if type == 'image':
                args_dict['searchType'] = 'image'
            res = service.cse().list(**args_dict).execute()
            for item in res['items']:
                results.append({
                    'title': item['title'],
                    'description': item['snippet'] if item.get('snippet') else "",
                    'url': item['link']
                })

        return results
    return google_search

