from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import ProtectedError
from .models import MountainRange, StartingPoint, Route
from .serializers import MountainRangeSerializer, StartingPointSerializer, RouteSerializer


class BaseListView(APIView):
    model = None
    serializer_class = None


    def get(self, request):
        items = self.model.objects.all()
        serializer = self.serializer_class(items, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response({"error": "Невалідні дані", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class BaseDetailView(APIView):
    model = None
    serializer_class = None
    resource_name = ""

    def get_object(self, pk):
        try:
            return self.model.objects.get(pk=pk)
        except self.model.DoesNotExist:
            return None

    def get(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"error": f"{self.resource_name} не знайдено"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(obj)
        return Response(serializer.data)

    def put(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"error": f"{self.resource_name} не знайдено"}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.serializer_class(obj, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({"error": "Невалідні дані", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"error": f"{self.resource_name} не знайдено"}, status=status.HTTP_404_NOT_FOUND)

        serializer = self.serializer_class(obj, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response({"error": "Невалідні дані", "details": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        obj = self.get_object(pk)
        if not obj:
            return Response({"error": f"{self.resource_name} не знайдено"}, status=status.HTTP_404_NOT_FOUND)
        try:
            obj.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except ProtectedError:
            return Response(
                {"error": f"Неможливо видалити {self.resource_name.lower()}, оскільки існують пов'язані маршрути"},
                status=status.HTTP_409_CONFLICT
            )


class MountainRangeList(BaseListView):
    model = MountainRange
    serializer_class = MountainRangeSerializer


class MountainRangeDetail(BaseDetailView):
    model = MountainRange
    serializer_class = MountainRangeSerializer
    resource_name = "Гірський масив"


class MountainRangeRoutesList(APIView):
    def get(self, request, pk):
        if not MountainRange.objects.filter(pk=pk).exists():
            return Response({"error": "Гірський масив не знайдено"}, status=status.HTTP_404_NOT_FOUND)

        routes = Route.objects.filter(mountain_range_id=pk)
        serializer = RouteSerializer(routes, many=True)
        return Response(serializer.data)


class StartingPointList(BaseListView):
    model = StartingPoint
    serializer_class = StartingPointSerializer


class StartingPointDetail(BaseDetailView):
    model = StartingPoint
    serializer_class = StartingPointSerializer
    resource_name = "Стартова точка"


class StartingPointRoutesList(APIView):
    def get(self, request, pk):
        if not StartingPoint.objects.filter(pk=pk).exists():
            return Response({"error": "Стартовий пункт не знайдено"}, status=status.HTTP_404_NOT_FOUND)

        routes = Route.objects.filter(starting_point_id=pk)
        serializer = RouteSerializer(routes, many=True)
        return Response(serializer.data)


class RouteList(BaseListView):
    model = Route
    serializer_class = RouteSerializer


class RouteDetail(BaseDetailView):
    model = Route
    serializer_class = RouteSerializer
    resource_name = "Маршрут"
