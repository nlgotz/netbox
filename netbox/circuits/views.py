from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import permission_required
from django.core.urlresolvers import reverse, resolve
from django.contrib import messages

from extras.models import Graph, GRAPH_TYPE_PROVIDER
from utilities.forms import ConfirmationForm
from utilities.views import (
    BulkDeleteView, BulkEditView, BulkImportView, ObjectDeleteView, ObjectEditView, ObjectListView,
)

from . import filters, forms, tables
from .models import Circuit, CircuitType, Provider, Termination


#
# Providers
#

class ProviderListView(ObjectListView):
    queryset = Provider.objects.annotate(count_circuits=Count('circuits'))
    filter = filters.ProviderFilter
    filter_form = forms.ProviderFilterForm
    table = tables.ProviderTable
    edit_permissions = ['circuits.change_provider', 'circuits.delete_provider']
    template_name = 'circuits/provider_list.html'


def provider(request, slug):

    provider = get_object_or_404(Provider, slug=slug)
    circuits = Circuit.objects.filter(provider=provider)
    show_graphs = Graph.objects.filter(type=GRAPH_TYPE_PROVIDER).exists()

    return render(request, 'circuits/provider.html', {
        'provider': provider,
        'circuits': circuits,
        'show_graphs': show_graphs,
    })


class ProviderEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'circuits.change_provider'
    model = Provider
    form_class = forms.ProviderForm
    template_name = 'circuits/provider_edit.html'
    cancel_url = 'circuits:provider_list'


class ProviderDeleteView(PermissionRequiredMixin, ObjectDeleteView):
    permission_required = 'circuits.delete_provider'
    model = Provider
    redirect_url = 'circuits:provider_list'


class ProviderBulkImportView(PermissionRequiredMixin, BulkImportView):
    permission_required = 'circuits.add_provider'
    form = forms.ProviderImportForm
    table = tables.ProviderTable
    template_name = 'circuits/provider_import.html'
    obj_list_url = 'circuits:provider_list'


class ProviderBulkEditView(PermissionRequiredMixin, BulkEditView):
    permission_required = 'circuits.change_provider'
    cls = Provider
    form = forms.ProviderBulkEditForm
    template_name = 'circuits/provider_bulk_edit.html'
    default_redirect_url = 'circuits:provider_list'


class ProviderBulkDeleteView(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'circuits.delete_provider'
    cls = Provider
    default_redirect_url = 'circuits:provider_list'


#
# Circuit Types
#

class CircuitTypeListView(ObjectListView):
    queryset = CircuitType.objects.annotate(circuit_count=Count('circuits'))
    table = tables.CircuitTypeTable
    edit_permissions = ['circuits.change_circuittype', 'circuits.delete_circuittype']
    template_name = 'circuits/circuittype_list.html'


class CircuitTypeEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'circuits.change_circuittype'
    model = CircuitType
    form_class = forms.CircuitTypeForm
    success_url = 'circuits:circuittype_list'
    cancel_url = 'circuits:circuittype_list'


class CircuitTypeBulkDeleteView(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'circuits.delete_circuittype'
    cls = CircuitType
    default_redirect_url = 'circuits:circuittype_list'


#
# Circuits
#

class CircuitListView(ObjectListView):
    queryset = Circuit.objects.select_related('provider', 'type', 'tenant').annotate(count_terminations=Count('terminations'))
    filter = filters.CircuitFilter
    filter_form = forms.CircuitFilterForm
    table = tables.CircuitTable
    edit_permissions = ['circuits.change_circuit', 'circuits.delete_circuit']
    template_name = 'circuits/circuit_list.html'


def circuit(request, pk):

    circuit = get_object_or_404(Circuit, pk=pk)

    return render(request, 'circuits/circuit.html', {
        'circuit': circuit,
    })


class CircuitEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'circuits.change_circuit'
    model = Circuit
    form_class = forms.CircuitForm
    fields_initial = ['site']
    template_name = 'circuits/circuit_edit.html'
    cancel_url = 'circuits:circuit_list'


class CircuitDeleteView(PermissionRequiredMixin, ObjectDeleteView):
    permission_required = 'circuits.delete_circuit'
    model = Circuit
    redirect_url = 'circuits:circuit_list'


class CircuitBulkImportView(PermissionRequiredMixin, BulkImportView):
    permission_required = 'circuits.add_circuit'
    form = forms.CircuitImportForm
    table = tables.CircuitTable
    template_name = 'circuits/circuit_import.html'
    obj_list_url = 'circuits:circuit_list'


class CircuitBulkEditView(PermissionRequiredMixin, BulkEditView):
    permission_required = 'circuits.change_circuit'
    cls = Circuit
    form = forms.CircuitBulkEditForm
    template_name = 'circuits/circuit_bulk_edit.html'
    default_redirect_url = 'circuits:circuit_list'


class CircuitBulkDeleteView(PermissionRequiredMixin, BulkDeleteView):
    permission_required = 'circuits.delete_circuit'
    cls = Circuit
    default_redirect_url = 'circuits:circuit_list'

#
# Terminations
#
@permission_required('circuits.change_circuit')
def termination_add(request, pk):

    circuit = get_object_or_404(Circuit, pk=pk)

    if request.method == 'POST':
        form = forms.TerminationForm(request.POST)
        if form.is_valid():
            if not form.errors:
                new_termination = form.save(commit=False)
                new_termination.circuit = circuit
                new_termination.save()
                if '_addanother' in request.POST:
                    return redirect('circuits:termination_add', pk=circuit.pk)
                else:
                    return redirect('circuits:circuit', pk=circuit.pk)

    else:
        form = forms.TerminationForm()

    return render(request, 'circuits/termination_edit.html', {
        'form': form,
        'obj_type': "Termination",
        'cancel_url': reverse('circuits:circuit', kwargs={'pk': circuit.pk}),
    })

class TerminationEditView(PermissionRequiredMixin, ObjectEditView):
    permission_required = 'circuits.change_circuit'
    model = Termination
    form_class = forms.TerminationForm
    fields_initial = ['site']
    template_name = 'circuits/termination_edit.html'
    cancel_url = 'circuits:circuit_list'

@permission_required('circuits.delete_circuit')
def termination_delete(request, pk):

    termination = get_object_or_404(Termination, pk=pk)

    if request.method == 'POST':
        form = ConfirmationForm(request.POST)
        if form.is_valid():
            termination.delete()
            messages.success(request, "Termination {0} has been deleted from {1}".format(termination, termination.circuit))
            return redirect('circuits:circuit', pk=termination.circuit.pk)

    else:
        form = ConfirmationForm()

    return render(request, 'circuits/termination_delete.html', {
        'termination': termination,
        'form': form,
        'cancel_url': reverse('circuits:circuit', kwargs={'pk': termination.circuit.pk}),
    })
