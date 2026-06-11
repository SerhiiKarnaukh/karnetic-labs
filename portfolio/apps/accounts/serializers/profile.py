from djoser.serializers import UserCreateSerializer


class ProfileCreateSerializer(UserCreateSerializer):

    class Meta(UserCreateSerializer.Meta):
        fields = ('id', 'email', 'username', 'password', 'first_name', 'last_name',)

    def create(self, validated_data):
        user = super().create(validated_data)
        return user
