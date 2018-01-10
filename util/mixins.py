from rest_framework import mixins

# CreateModelUpdateByMixin

class CreateModelUpdateByMixin(mixins.CreateModelMixin):

    def perform_create(self, serializer):
        
        serializer.save(updated_by=self.request.user)
    
# UpdateModelUpdateByMixin

class UpdateModelUpdateByMixin(mixins.UpdateModelMixin):

    def perform_update(self, serializer):
        
        serializer.save(updated_by=self.request.user)

