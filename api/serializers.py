from rest_framework import serializers
from .models import User,Group,Expense,ExpenseSplit
from django.contrib.auth.hashers import check_password

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['name', 'email', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            name=validated_data['name']
        )
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self,data):
        try:
            user = User.objects.get(email=data['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError('Invalid email or password')
        if not check_password(data['password'],user.password):
            raise serializers.ValidationError('Invalid email or password')
        return user

class GroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'name', 'created_by', 'members', 'created_at']
        read_only_fields = ['created_by', 'created_at']
        extra_kwargs = {'members': {'required': False}}
        
class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ['id', 'group', 'paid_by', 'amount', 'category', 'description', 'receipt_url', 'created_at']
        read_only_fields = ['paid_by', 'created_at']
    