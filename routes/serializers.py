from rest_framework import serializers
from .models import MountainRange, StartingPoint, Route, Gear


class MountainRangeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MountainRange
        fields = '__all__'


class StartingPointSerializer(serializers.ModelSerializer):
    class Meta:
        model = StartingPoint
        fields = '__all__'


class RouteSerializer(serializers.ModelSerializer):
    gear = serializers.ListField(child=serializers.CharField(), write_only=True, required=False)

    class Meta:
        model = Route
        fields = '__all__'

    def create(self, validated_data):
        gear_data = validated_data.pop('gear', [])
        route = super().create(validated_data)

        for item in gear_data:
            gear_tuple = Gear.objects.get_or_create(name=item)
            gear_obj = gear_tuple[0]
            route.gear.add(gear_obj)

        return route

    def update(self, instance, validated_data):
        gear_data = validated_data.pop('gear', None)
        instance = super().update(instance, validated_data)
        if gear_data is not None:
            instance.gear.clear()
            for item in gear_data:
                gear_tuple = Gear.objects.get_or_create(name=item)
                gear_obj = gear_tuple[0]
                instance.gear.add(gear_obj)

        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['gear'] = [gear.name for gear in instance.gear.all()]
        return rep
