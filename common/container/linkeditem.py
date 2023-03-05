from urllib.parse import urlparse


class LinkedItem:
    def __init__(self, surface_form, uris):
        self.surface_form = surface_form
        self.uris = uris

    def top_uris(self, top=1):
        return self.uris[:int(top * len(self.uris))]

    def contains_uri(self, uri):
        """
        Whether the uri exists in the list of uris
        :param uri:
        :return: Bool
        """
        
        #return uri in self.uris

        try:
            result = urlparse(uri)
            return all([result.scheme, result.netloc])
        except ValueError:
            return False

    @staticmethod
    def list_contains_uris(linkeditem_list, uris):
        """
        Returns the linkedItems that contain any of the uris,
        but only one linkedItem per uri
        :param linkeditem_list: List of LinkedItem
        :param uris:
        :return:
        """
        output = []
        for uri in sorted(uris, key=lambda x: len(str(x)), reverse=True):
            for item in linkeditem_list:
                item = item['uri']
                #print("(line 40 )list_contains_uris item = ",item)
                if item not in output: #and contains_uri(item)
                    output.append(item)
                    #print("(line 43 ) appending item",item ,"to output", output)
                    break
        #print("(line 45) this is output in list_contains_uris", output)
        return output