"""
Tests for SaaS system schema templates.
Verifies schema validity and realistic data generation for HubSpot and Salesforce templates.
"""

import pytest
from pathlib import Path
from jafgen.schema.yaml_loader import YAMLSchemaLoader
from jafgen.schema.discovery import SchemaDiscoveryEngine
from jafgen.generation.data_generator import DataGenerator
from jafgen.generation.mimesis_engine import MimesisEngine
from jafgen.generation.link_resolver import LinkResolver


class TestSaaSTemplateSchemas:
    """Test SaaS template schema validity and structure."""
    
    @pytest.fixture
    def saas_templates_dir(self):
        """Path to SaaS templates directory."""
        return Path("schemas/saas-templates")
    
    @pytest.fixture
    def schema_loader(self):
        """Schema loader instance."""
        return YAMLSchemaLoader()
    
    @pytest.fixture
    def schema_discovery(self):
        """Schema discovery instance."""
        return SchemaDiscoveryEngine()
    
    def test_hubspot_schemas_exist(self, saas_templates_dir):
        """Test that all HubSpot schema files exist."""
        hubspot_dir = saas_templates_dir / "hubspot"
        
        expected_files = ["contacts.yaml", "companies.yaml", "deals.yaml"]
        for file_name in expected_files:
            schema_file = hubspot_dir / file_name
            assert schema_file.exists(), f"HubSpot schema file {file_name} should exist"
    
    def test_salesforce_schemas_exist(self, saas_templates_dir):
        """Test that all Salesforce schema files exist."""
        salesforce_dir = saas_templates_dir / "salesforce"
        
        expected_files = ["accounts.yaml", "contacts.yaml", "opportunities.yaml"]
        for file_name in expected_files:
            schema_file = salesforce_dir / file_name
            assert schema_file.exists(), f"Salesforce schema file {file_name} should exist"
    
    def test_hubspot_contacts_schema_valid(self, saas_templates_dir, schema_loader):
        """Test HubSpot contacts schema is valid."""
        schema_path = saas_templates_dir / "hubspot" / "contacts.yaml"
        schema = schema_loader.load_schema(schema_path)
        
        # Verify system configuration
        assert schema.name == "hubspot-contacts"
        assert schema.version == "1.0.0"
        assert schema.seed == 42
        
        # Verify entities
        assert "contacts" in schema.entities
        contacts_entity = schema.entities["contacts"]
        assert contacts_entity.count == 1000
        
        # Verify key attributes
        required_attrs = ["id", "firstname", "lastname", "email", "lead_status", "lifecycle_stage", "createdate"]
        for attr in required_attrs:
            assert attr in contacts_entity.attributes, f"Required attribute {attr} missing"
            assert contacts_entity.attributes[attr].required, f"Attribute {attr} should be required"
    
    def test_hubspot_companies_schema_valid(self, saas_templates_dir, schema_loader):
        """Test HubSpot companies schema is valid."""
        schema_path = saas_templates_dir / "hubspot" / "companies.yaml"
        schema = schema_loader.load_schema(schema_path)
        
        # Verify system configuration
        assert schema.name == "hubspot-companies"
        assert schema.version == "1.0.0"
        
        # Verify entities
        assert "companies" in schema.entities
        companies_entity = schema.entities["companies"]
        assert companies_entity.count == 200
        
        # Verify key attributes
        required_attrs = ["id", "name", "lifecyclestage", "createdate"]
        for attr in required_attrs:
            assert attr in companies_entity.attributes, f"Required attribute {attr} missing"
    
    def test_hubspot_deals_schema_valid(self, saas_templates_dir, schema_loader):
        """Test HubSpot deals schema is valid."""
        schema_path = saas_templates_dir / "hubspot" / "deals.yaml"
        schema = schema_loader.load_schema(schema_path)
        
        # Verify system configuration
        assert schema.name == "hubspot-deals"
        
        # Verify entities
        assert "deals" in schema.entities
        deals_entity = schema.entities["deals"]
        assert deals_entity.count == 500
        
        # Verify key attributes
        required_attrs = ["id", "dealname", "hubspot_owner_id", "amount", "dealstage", "pipeline", "createdate"]
        for attr in required_attrs:
            assert attr in deals_entity.attributes, f"Required attribute {attr} missing"
    
    def test_salesforce_accounts_schema_valid(self, saas_templates_dir, schema_loader):
        """Test Salesforce accounts schema is valid."""
        schema_path = saas_templates_dir / "salesforce" / "accounts.yaml"
        schema = schema_loader.load_schema(schema_path)
        
        # Verify system configuration
        assert schema.name == "salesforce-accounts"
        
        # Verify entities
        assert "accounts" in schema.entities
        accounts_entity = schema.entities["accounts"]
        assert accounts_entity.count == 300
        
        # Verify key attributes
        required_attrs = ["Id", "Name", "OwnerId", "CreatedDate", "LastModifiedDate"]
        for attr in required_attrs:
            assert attr in accounts_entity.attributes, f"Required attribute {attr} missing"
    
    def test_salesforce_contacts_schema_valid(self, saas_templates_dir, schema_loader):
        """Test Salesforce contacts schema is valid."""
        schema_path = saas_templates_dir / "salesforce" / "contacts.yaml"
        schema = schema_loader.load_schema(schema_path)
        
        # Verify system configuration
        assert schema.name == "salesforce-contacts"
        
        # Verify entities
        assert "contacts" in schema.entities
        contacts_entity = schema.entities["contacts"]
        assert contacts_entity.count == 1200
        
        # Verify key attributes
        required_attrs = ["Id", "FirstName", "LastName", "OwnerId", "CreatedDate", "LastModifiedDate"]
        for attr in required_attrs:
            assert attr in contacts_entity.attributes, f"Required attribute {attr} missing"
    
    def test_salesforce_opportunities_schema_valid(self, saas_templates_dir, schema_loader):
        """Test Salesforce opportunities schema is valid."""
        schema_path = saas_templates_dir / "salesforce" / "opportunities.yaml"
        schema = schema_loader.load_schema(schema_path)
        
        # Verify system configuration
        assert schema.name == "salesforce-opportunities"
        
        # Verify entities
        assert "opportunities" in schema.entities
        opportunities_entity = schema.entities["opportunities"]
        assert opportunities_entity.count == 800
        
        # Verify key attributes
        required_attrs = ["Id", "Name", "AccountId", "OwnerId", "CloseDate", "StageName", "CreatedDate"]
        for attr in required_attrs:
            assert attr in opportunities_entity.attributes, f"Required attribute {attr} missing"


class TestSaaSTemplateDataGeneration:
    """Test data generation for SaaS templates."""
    
    @pytest.fixture
    def mimesis_engine(self):
        """Mimesis engine with fixed seed."""
        return MimesisEngine(seed=42)
    
    @pytest.fixture
    def link_resolver(self):
        """Link resolver instance."""
        return LinkResolver()
    
    @pytest.fixture
    def data_generator(self, mimesis_engine, link_resolver):
        """Data generator instance."""
        return DataGenerator(mimesis_engine, link_resolver)
    
    @pytest.fixture
    def schema_loader(self):
        """Schema loader instance."""
        return YAMLSchemaLoader()
    
    def test_hubspot_contacts_data_generation(self, data_generator, schema_loader):
        """Test data generation for HubSpot contacts."""
        schema_path = Path("schemas/saas-templates/hubspot/contacts.yaml")
        schema = schema_loader.load_schema(schema_path)
        
        # Generate small sample for testing
        contacts_config = schema.entities["contacts"]
        contacts_config.count = 10  # Reduce for testing
        
        generated_data = data_generator.generate_entity(contacts_config)
        
        assert len(generated_data) == 10
        
        # Verify required fields are present and not null
        for contact in generated_data:
            assert contact["id"] is not None
            assert contact["firstname"] is not None
            assert contact["lastname"] is not None
            assert contact["email"] is not None
            assert contact["lead_status"] in ["NEW", "OPEN", "IN_PROGRESS", "OPEN_DEAL", "UNQUALIFIED", "ATTEMPTED_TO_CONTACT", "CONNECTED", "BAD_TIMING"]
            assert contact["lifecycle_stage"] in ["subscriber", "lead", "marketingqualifiedlead", "salesqualifiedlead", "opportunity", "customer", "evangelist", "other"]
        
        # Verify unique constraints
        ids = [contact["id"] for contact in generated_data]
        emails = [contact["email"] for contact in generated_data]
        assert len(set(ids)) == len(ids), "IDs should be unique"
        assert len(set(emails)) == len(emails), "Emails should be unique"
    
    def test_salesforce_accounts_data_generation(self, data_generator, schema_loader):
        """Test data generation for Salesforce accounts."""
        schema_path = Path("schemas/saas-templates/salesforce/accounts.yaml")
        schema = schema_loader.load_schema(schema_path)
        
        # Generate small sample for testing
        accounts_config = schema.entities["accounts"]
        accounts_config.count = 5  # Reduce for testing
        
        generated_data = data_generator.generate_entity(accounts_config)
        
        assert len(generated_data) == 5
        
        # Verify required fields are present and not null
        for account in generated_data:
            assert account["Id"] is not None
            assert account["Name"] is not None
            assert account["OwnerId"] is not None
            assert account["CreatedDate"] is not None
            assert account["LastModifiedDate"] is not None
        
        # Verify unique constraints
        ids = [account["Id"] for account in generated_data]
        names = [account["Name"] for account in generated_data]
        assert len(set(ids)) == len(ids), "IDs should be unique"
        assert len(set(names)) == len(names), "Names should be unique"
    
    def test_hubspot_deals_realistic_amounts(self, data_generator, schema_loader):
        """Test that HubSpot deals generate realistic amounts."""
        schema_path = Path("schemas/saas-templates/hubspot/deals.yaml")
        schema = schema_loader.load_schema(schema_path)
        
        deals_config = schema.entities["deals"]
        deals_config.count = 20  # Reduce for testing
        
        generated_data = data_generator.generate_entity(deals_config)
        
        # Verify amounts are within expected range
        for deal in generated_data:
            amount = deal["amount"]
            assert 500 <= amount <= 500000, f"Deal amount {amount} should be between 500 and 500000"
    
    def test_salesforce_opportunities_stage_probability_consistency(self, data_generator, schema_loader):
        """Test that Salesforce opportunities have consistent stage and probability."""
        schema_path = Path("schemas/saas-templates/salesforce/opportunities.yaml")
        schema = schema_loader.load_schema(schema_path)
        
        opportunities_config = schema.entities["opportunities"]
        opportunities_config.count = 15  # Reduce for testing
        
        generated_data = data_generator.generate_entity(opportunities_config)
        
        # Verify stage names are valid
        valid_stages = ["Prospecting", "Qualification", "Needs Analysis", "Value Proposition", 
                       "Id. Decision Makers", "Perception Analysis", "Proposal/Price Quote", 
                       "Negotiation/Review", "Closed Won", "Closed Lost"]
        
        for opportunity in generated_data:
            assert opportunity["StageName"] in valid_stages
            if opportunity.get("Probability") is not None:
                assert 0 <= opportunity["Probability"] <= 100
    
    def test_schema_deterministic_generation(self, schema_loader):
        """Test that schemas generate deterministic data with same seed."""
        schema_path = Path("schemas/saas-templates/hubspot/contacts.yaml")
        schema = schema_loader.load_schema(schema_path)
        
        # Generate data twice with same seed
        engine1 = MimesisEngine(seed=42)
        resolver1 = LinkResolver()
        generator1 = DataGenerator(engine1, resolver1)
        
        engine2 = MimesisEngine(seed=42)
        resolver2 = LinkResolver()
        generator2 = DataGenerator(engine2, resolver2)
        
        contacts_config = schema.entities["contacts"]
        contacts_config.count = 5  # Small sample
        
        data1 = generator1.generate_entity(contacts_config)
        data2 = generator2.generate_entity(contacts_config)
        
        # Should generate identical data
        assert len(data1) == len(data2)
        for i in range(len(data1)):
            assert data1[i]["firstname"] == data2[i]["firstname"]
            assert data1[i]["lastname"] == data2[i]["lastname"]
            assert data1[i]["email"] == data2[i]["email"]


class TestXeroTemplateSchemas:
    """Test Xero template schema validity and structure."""
    
    @pytest.fixture
    def saas_templates_dir(self):
        """Path to SaaS templates directory."""
        return Path("schemas/saas-templates")
    
    @pytest.fixture
    def schema_loader(self):
        """Schema loader instance."""
        return YAMLSchemaLoader()
    
    def test_xero_schemas_exist(self, saas_templates_dir):
        """Test that all Xero schema files exist."""
        xero_dir = saas_templates_dir / "xero"
        
        expected_files = ["customers.yaml", "invoices.yaml", "payments.yaml"]
        for file_name in expected_files:
            schema_file = xero_dir / file_name
            assert schema_file.exists(), f"Xero schema file {file_name} should exist"
    
    def test_xero_customers_schema_valid(self, saas_templates_dir, schema_loader):
        """Test Xero customers schema is valid."""
        schema_path = saas_templates_dir / "xero" / "customers.yaml"
        schema = schema_loader.load_schema(schema_path)
        
        # Verify system configuration
        assert schema.name == "xero-customers"
        assert schema.version == "1.0.0"
        
        # Verify entities
        assert "customers" in schema.entities
        customers_entity = schema.entities["customers"]
        assert customers_entity.count == 500
        
        # Verify key attributes
        required_attrs = ["ContactID", "Name", "ContactStatus", "IsCustomer", "UpdatedDateUTC"]
        for attr in required_attrs:
            assert attr in customers_entity.attributes, f"Required attribute {attr} missing"
    
    def test_xero_invoices_schema_valid(self, saas_templates_dir, schema_loader):
        """Test Xero invoices schema is valid."""
        schema_path = saas_templates_dir / "xero" / "invoices.yaml"
        schema = schema_loader.load_schema(schema_path)
        
        # Verify system configuration
        assert schema.name == "xero-invoices"
        
        # Verify entities
        assert "invoices" in schema.entities
        invoices_entity = schema.entities["invoices"]
        assert invoices_entity.count == 1200
        
        # Verify key attributes
        required_attrs = ["InvoiceID", "InvoiceNumber", "Type", "ContactID", "Date", "SubTotal", "Total", "Status"]
        for attr in required_attrs:
            assert attr in invoices_entity.attributes, f"Required attribute {attr} missing"
    
    def test_xero_payments_schema_valid(self, saas_templates_dir, schema_loader):
        """Test Xero payments schema is valid."""
        schema_path = saas_templates_dir / "xero" / "payments.yaml"
        schema = schema_loader.load_schema(schema_path)
        
        # Verify system configuration
        assert schema.name == "xero-payments"
        
        # Verify entities
        assert "payments" in schema.entities
        payments_entity = schema.entities["payments"]
        assert payments_entity.count == 800
        
        # Verify key attributes
        required_attrs = ["PaymentID", "InvoiceID", "AccountID", "Date", "Amount", "Status"]
        for attr in required_attrs:
            assert attr in payments_entity.attributes, f"Required attribute {attr} missing"


class TestHuntrTemplateSchemas:
    """Test Huntr template schema validity and structure."""
    
    @pytest.fixture
    def saas_templates_dir(self):
        """Path to SaaS templates directory."""
        return Path("schemas/saas-templates")
    
    @pytest.fixture
    def schema_loader(self):
        """Schema loader instance."""
        return YAMLSchemaLoader()
    
    def test_huntr_schemas_exist(self, saas_templates_dir):
        """Test that all Huntr schema files exist."""
        huntr_dir = saas_templates_dir / "huntr"
        
        expected_files = ["jobs.yaml", "activities.yaml", "contacts.yaml"]
        for file_name in expected_files:
            schema_file = huntr_dir / file_name
            assert schema_file.exists(), f"Huntr schema file {file_name} should exist"
    
    def test_huntr_jobs_schema_valid(self, saas_templates_dir, schema_loader):
        """Test Huntr jobs schema is valid."""
        schema_path = saas_templates_dir / "huntr" / "jobs.yaml"
        schema = schema_loader.load_schema(schema_path)
        
        # Verify system configuration
        assert schema.name == "huntr-jobs"
        
        # Verify entities
        assert "jobs" in schema.entities
        jobs_entity = schema.entities["jobs"]
        assert jobs_entity.count == 300
        
        # Verify key attributes
        required_attrs = ["id", "title", "company", "employment_type", "status", "date_added"]
        for attr in required_attrs:
            assert attr in jobs_entity.attributes, f"Required attribute {attr} missing"
    
    def test_huntr_activities_schema_valid(self, saas_templates_dir, schema_loader):
        """Test Huntr activities schema is valid."""
        schema_path = saas_templates_dir / "huntr" / "activities.yaml"
        schema = schema_loader.load_schema(schema_path)
        
        # Verify system configuration
        assert schema.name == "huntr-activities"
        
        # Verify entities
        assert "activities" in schema.entities
        activities_entity = schema.entities["activities"]
        assert activities_entity.count == 800
        
        # Verify key attributes
        required_attrs = ["id", "job_id", "type", "status", "date", "created_at"]
        for attr in required_attrs:
            assert attr in activities_entity.attributes, f"Required attribute {attr} missing"
    
    def test_huntr_contacts_schema_valid(self, saas_templates_dir, schema_loader):
        """Test Huntr contacts schema is valid."""
        schema_path = saas_templates_dir / "huntr" / "contacts.yaml"
        schema = schema_loader.load_schema(schema_path)
        
        # Verify system configuration
        assert schema.name == "huntr-contacts"
        
        # Verify entities
        assert "contacts" in schema.entities
        contacts_entity = schema.entities["contacts"]
        assert contacts_entity.count == 400
        
        # Verify key attributes
        required_attrs = ["id", "first_name", "last_name", "full_name", "created_at"]
        for attr in required_attrs:
            assert attr in contacts_entity.attributes, f"Required attribute {attr} missing"


class TestSaaSTemplateIntegration:
    """Integration tests for SaaS template data generation."""
    
    @pytest.fixture
    def mimesis_engine(self):
        """Mimesis engine with fixed seed."""
        return MimesisEngine(seed=42)
    
    @pytest.fixture
    def link_resolver(self):
        """Link resolver instance."""
        return LinkResolver()
    
    @pytest.fixture
    def data_generator(self, mimesis_engine, link_resolver):
        """Data generator instance."""
        return DataGenerator(mimesis_engine, link_resolver)
    
    @pytest.fixture
    def schema_loader(self):
        """Schema loader instance."""
        return YAMLSchemaLoader()
    
    def test_xero_customers_data_generation(self, data_generator, schema_loader):
        """Test data generation for Xero customers."""
        schema_path = Path("schemas/saas-templates/xero/customers.yaml")
        schema = schema_loader.load_schema(schema_path)
        
        # Generate small sample for testing
        customers_config = schema.entities["customers"]
        customers_config.count = 10  # Reduce for testing
        
        generated_data = data_generator.generate_entity(customers_config)
        
        assert len(generated_data) == 10
        
        # Verify required fields are present and not null
        for customer in generated_data:
            assert customer["ContactID"] is not None
            assert customer["Name"] is not None
            assert customer["ContactStatus"] in ["ACTIVE", "ARCHIVED", "GDPRREQUEST"]
            assert customer["IsCustomer"] in [True, False]
            assert customer["UpdatedDateUTC"] is not None
        
        # Verify unique constraints
        contact_ids = [customer["ContactID"] for customer in generated_data]
        assert len(set(contact_ids)) == len(contact_ids), "ContactIDs should be unique"
    
    def test_huntr_jobs_realistic_salaries(self, data_generator, schema_loader):
        """Test that Huntr jobs generate realistic salary ranges."""
        schema_path = Path("schemas/saas-templates/huntr/jobs.yaml")
        schema = schema_loader.load_schema(schema_path)
        
        jobs_config = schema.entities["jobs"]
        jobs_config.count = 20  # Reduce for testing
        
        generated_data = data_generator.generate_entity(jobs_config)
        
        # Verify salary ranges are realistic
        for job in generated_data:
            if job.get("salary_min") is not None:
                assert 30000 <= job["salary_min"] <= 200000
            if job.get("salary_max") is not None:
                assert 40000 <= job["salary_max"] <= 300000
            assert job["status"] in ["WISHLIST", "APPLIED", "PHONE_SCREEN", "ON_SITE", "OFFER", "REJECTED", "ARCHIVED"]
    
    def test_xero_invoices_financial_consistency(self, data_generator, schema_loader):
        """Test that Xero invoices have consistent financial amounts."""
        schema_path = Path("schemas/saas-templates/xero/invoices.yaml")
        schema = schema_loader.load_schema(schema_path)
        
        invoices_config = schema.entities["invoices"]
        invoices_config.count = 15  # Reduce for testing
        
        generated_data = data_generator.generate_entity(invoices_config)
        
        # Verify financial consistency
        for invoice in generated_data:
            assert invoice["SubTotal"] >= 10.00
            assert invoice["Total"] >= 10.00
            assert invoice["AmountDue"] >= 0.00
            assert invoice["AmountPaid"] >= 0.00
            assert invoice["Status"] in ["DRAFT", "SUBMITTED", "AUTHORISED", "PAID", "VOIDED", "DELETED"]
            assert invoice["Type"] in ["ACCPAY", "ACCPAYCREDIT", "ACCREC", "ACCRECCREDIT"]