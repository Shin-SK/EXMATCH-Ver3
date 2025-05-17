# core/filters.py
import django_filters
from django_filters import CharFilter, NumberFilter, ChoiceFilter, MultipleChoiceFilter
from django import forms  # ★ ここがポイント: Djangoのフォームウィジェットを使う
from .models import UserProfile, ProfileField
from .utils import haversine_distance
from .widgets import CustomRadio

class DynamicProfileFilter(django_filters.FilterSet):

    RADIUS_CHOICES = [
        ('1',  '1 km'),
        ('5',  '5 km'),
        ('10', '10 km'),
        ('30', '30 km'),
        ('100','100 km'),  # or '0' / '' = 制限なし
    ]

    # ▼ NumberFilter → ChoiceFilter に変更
    radius = django_filters.ChoiceFilter(
        choices=RADIUS_CHOICES,
        widget=forms.RadioSelect,
        label='距離 (半径)',
        method='filter_by_distance',
    )

    class Meta:
        model  = UserProfile
        fields = ['radius']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # ▼ Adminから追加したカスタムフィールドを拾い、動的にフォーム項目を生成
        for pf in ProfileField.objects.all():
            field_key = pf.field_key

            # 同名フィルターが既にあればスキップ
            if field_key in self.filters:
                continue

            # 改行区切りの選択肢をリスト化
            raw_choices = [c.strip() for c in pf.field_choices.split('\n') if c.strip()]
            choices = [(c, c) for c in raw_choices]  # ChoiceFilter/MultipleChoiceFilter用 (value, label)

            if pf.field_type == 'radio':
                # 単一選択をラジオボタンで表示
                self.filters[field_key] = ChoiceFilter(
                    choices=choices,
                    widget=forms.RadioSelect,  # ★ ラジオボタン
                    method=self.make_filter_method_exact(field_key),
                    label=pf.field_label
                )
            elif pf.field_type == 'select':
                # 単一選択をセレクトボックスで表示
                self.filters[field_key] = ChoiceFilter(
                    choices=choices,
                    widget=forms.Select,  # ★ 通常の<select>
                    method=self.make_filter_method_exact(field_key),
                    label=pf.field_label
                )
            elif pf.field_type == 'checkbox':
                # 複数選択をチェックボックスで表示
                self.filters[field_key] = MultipleChoiceFilter(
                    choices=choices,
                    widget=forms.CheckboxSelectMultiple,  # ★ チェックボックス
                    method=self.make_filter_method_checkbox(field_key),
                    label=pf.field_label
                )
            else:
                # text の場合はフリーテキスト検索 -> CharFilter
                self.filters[field_key] = CharFilter(
                    method=self.make_filter_method_text(field_key),
                    label=pf.field_label
                )

    # ---------------------------
    # 各フィールドタイプに応じたフィルタリング用メソッド
    # ---------------------------
    def make_filter_method_text(self, field_key):
        """profilefieldvalue__value に部分一致 (icontains)"""
        def _filter_method(queryset, name, value):
            if not value:
                return queryset
            return queryset.filter(
                profilefieldvalue__field__field_key=field_key,
                profilefieldvalue__value__icontains=value
            ).distinct()
        return _filter_method

    def make_filter_method_exact(self, field_key):
        """select / radio 用 -> 完全一致"""
        def _filter_method(queryset, name, value):
            if not value:
                return queryset
            return queryset.filter(
                profilefieldvalue__field__field_key=field_key,
                profilefieldvalue__value=value
            ).distinct()
        return _filter_method

    def make_filter_method_checkbox(self, field_key):
        """
        checkbox（複数選択）で選んだ中のいずれかが含まれるレコードをヒットさせる。
        DBでは,区切りで保存されている想定なので icontains でOR検索する例。
        """
        def _filter_method(queryset, name, value_list):
            if not value_list:
                return queryset
            from django.db.models import Q
            q = Q()
            for v in value_list:
                # どれか1つでも value に含まれていればOK(OR条件)
                q |= Q(
                    profilefieldvalue__field__field_key=field_key,
                    profilefieldvalue__value__icontains=v
                )
            return queryset.filter(q).distinct()
        return _filter_method

    # ---------------------------
    # 既存: 距離で絞り込み
    # ---------------------------
    def filter_by_distance(self, queryset, name, value):
        # ------- ① 受け取った値を即ログ ----------
        lat_str = self.request.GET.get("lat")
        lon_str = self.request.GET.get("lon")
        print("★params:", lat_str, lon_str, value)   # ← ここ

        if not (lat_str and lon_str and value):
            print("★skip: lat/lon/value 無し")
            return queryset

        try:
            user_lat = float(lat_str)
            user_lon = float(lon_str)
            radius_km = float(value)                 # Choice の value を km として解釈
        except ValueError:
            print("★skip: value 変換失敗 ->", value)
            return queryset

        within = []
        for prof in queryset:
            if prof.latitude and prof.longitude:
                dist = haversine_distance(
                    user_lat, user_lon, prof.latitude, prof.longitude
                )
                # ------- ② レコード毎の距離と判定 ----------
                print(f"★{prof.id=} {prof.nickname=} {dist=:.2f} km {radius_km=}")

                if dist <= radius_km:
                    within.append(prof.id)

        print("★hit ids:", within)
        return queryset.filter(id__in=within)

