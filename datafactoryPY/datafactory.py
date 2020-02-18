# datafactory.py file in creating datafactory with python
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.datafactory import DataFactoryManagementClient
from azure.mgmt.datafactory.models import *
from datetime import datetime, timedelta
import time

def print_item(group):
    """ print an azure object instance"""
    print("\tName: {}".format(group.name))
    print("\tId: {}".format(group.id))
    if hasattr(group, 'location'):
        print("\tLocation: {}".format(group.location))
    if hasattr(group, 'tags'):
        print("\tTags: {}".format(group.tags))
    if hasattr(group, 'properties'):
        print_properties(group.properties)

def print_properties(props):
    """ print a resource group properties instance """
    if props and hasattr(props, 'provisioning_state') and props.provisioning_state:
        print("\tProperties:")
        print("\t\tProvisioning State: {}".format(props.provisioning_state))
    print("\n\n")

def print_activity_run_details(activity_run):
    """print activity run"""
    print("\n\tActivity run details\n")
    print("\tActivity run status: {}".format(activity_run.status))
    if activity_run.status == 'Succeeded':
        print("\tNumber of bytes read: {}".format(activity_run.output['dataRead']))
        print("\tNumber of bytes written: {}".format(activity_run.output['dataWritten']))
        print("\tCopy duration: {}".format(activity_run.output['copyDuration']))
    else:
        print("\tErrors: {}".format(activity_run.error['message']))


# DataFactoryManagementClient class creates datafactory, linked service, datasets, pipeline etc, can also use to monitor
def main():

    # Azure subscription ID
    subscription_id = '3a2a1fce-48d6-4e09-bfd9-b20a33a2a813'

    # This program creates this resource group. If it's an existing resource group, comment out the code that creates the resource group
    rg_name = 'ADFTutorialResourceGroup'

    # The data factory name. It must be globally unique.
    df_name = 'PythonDFTomAlly'

    # Specify your Active Directory client ID, client secret, and tenant ID
    credentials = ServicePrincipalCredentials(client_id='a6b5bdef-6233-4115-b503-12f2ab45addf', secret='?UOHlwRhlfKH@tAV9k_[cCgdFC3jPl24', tenant='efee43ad-8ca6-4bbd-b90e-634e62d519f4')
    resource_client = ResourceManagementClient(credentials, subscription_id)
    adf_client = DataFactoryManagementClient(credentials, subscription_id)

    rg_params = {'location':'eastus'}
    df_params = {'location':'eastus'}

    # create the resource group
    # comment out if the resource group already exits
    resource_client.resource_groups.create_or_update(rg_name, rg_params)

    #Create a data factory
    df_resource = Factory(location='eastus')
    df = adf_client.factories.create_or_update(rg_name, df_name, df_resource)
    print_item(df)
    while df.provisioning_state != 'Succeeded':
        df = adf_client.factories.get(rg_name, df_name)
        time.sleep(1)

    # create azure storage linked service
    ls_name = 'storageLinkedService'

    # specify name and key of your storage account
    storage_string = SecureString(value='DefaultEndpointsProtocol=https;AccountName=storeul2stovu6ecnm;AccountKey=bbtovaufTSczIU3JRoGpo9nv2TA5Zl2LVMU3MGolRgyoX6hBkJ4jtWzstc6/tUZhaYBd52dHhN0+WX+f5ui3KQ==')

    ls_azure_storage = AzureStorageLinkedService(connection_string=storage_string)
    ls = adf_client.linked_services.create_or_update(rg_name, df_name, ls_name, ls_azure_storage)
    print_item(ls)

    # create azure blob dataset (input)
    ds_name = "ds_in"
    ds_ls = LinkedServiceReference(reference_name=ls_name)
    blob_path = "adfv2tutorial/input"
    blob_filename = "input.txt"
    ds_azure_blob = AzureBlobDataset(linked_service_name=ds_ls, folder_path=blob_path, file_name=blob_filename)
    ds = adf_client.datasets.create_or_update(rg_name, df_name, ds_name, ds_azure_blob)
    print_item(ds)

    # create azure blob dataset (output)
    dsOut_name = "ds_out"
    output_blobpath = 'adfv2tutorial/output'
    dsOut_azure_blob = AzureBlobDataset(linked_service_name=ds_ls, folder_path=output_blobpath)
    dsOut = adf_client.datasets.create_or_update(rg_name, df_name, dsOut_name, dsOut_azure_blob)
    print_item(dsOut)

    # create pipeline with copy activity
    act_name = "copyBlobtoBlob"
    blob_source = BlobSource()
    blob_sink = BlobSink()
    dsin_ref = DatasetReference(reference_name=ds_name)
    dsOut_ref = DatasetReference(reference_name=dsOut_name)
    copy_activity = CopyActivity(name=act_name, inputs=[dsin_ref], outputs=[dsOut_ref], source=blob_source, sink=blob_sink)

    p_name = 'copyPipeline'
    params_for_pipeline = {}
    p_obj = PipelineResource(activities=[copy_activity], parameters=params_for_pipeline)
    p = adf_client.pipelines.create_or_update(rg_name, df_name, p_name, p_obj)
    print_item(p)

    #create pipeline run
    run_response = adf_client.pipelines.create_run(rg_name, df_name, p_name, parameters={})

    #Monitor the pipeline run
    time.sleep(30)
    pipeline_run = adf_client.pipeline_runs.get(rg_name, df_name, run_response.run_id)
    print("\n\tPipeline run status: {}".format(pipeline_run.status))
    filter_params = RunFilterParameters(
        last_updated_after=datetime.now() - timedelta(1), last_updated_before=datetime.now() + timedelta(1))
    query_response = adf_client.activity_runs.query_by_pipeline_run(
        rg_name, df_name, pipeline_run.run_id, filter_params)
    print_activity_run_details(query_response.value[0])

if __name__ == "__main__":
    main()
