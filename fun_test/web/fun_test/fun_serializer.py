def model_instance_to_dict(self):   # Only used by cases that do not inherit from FunModel
    result = {}
    fields = self._meta.get_fields()
    for field in fields:
        result[field.name] = getattr(self, field.name)
    return result
