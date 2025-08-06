#!/usr/bin/env python3
"""
Debug script to test validation logic for 425 HANDYMAN SERVICES LLC
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.contractor_service import ContractorService
from src.database.models import Contractor
from src.database.connection import db_pool

async def debug_validation():
    """Debug validation for 425 HANDYMAN SERVICES LLC"""
    
    # Initialize database connection
    await db_pool.initialize()
    
    # Get contractor data
    query = """
    SELECT * FROM contractors 
    WHERE business_name = '425 HANDYMAN SERVICES LLC'
    """
    row = await db_pool.fetchrow(query)
    
    if not row:
        print("❌ Contractor not found")
        return
    
    # Create contractor object
    contractor = Contractor(
        id=row['id'],
        business_name=row['business_name'],
        contractor_license_number=row['contractor_license_number'],
        address1=row['address1'],
        city=row['city'],
        state=row['state'],
        zip=row['zip'],
        phone_number=row['phone_number'],
        primary_principal_name=row['primary_principal_name'],
        website_url='https://www.425handymanservices.com/',
        website_status='found'
    )
    
    # Website content from the search results
    website_content = """
    Skip to main content 

     425 Handyman Services 

    * Home
    * Services
    * Gallery
    * Contact
    * FAQs

    * Home
    * Services
    * Gallery
    * Contact
    * FAQs

    #  425 Handyman Services 

    Our handyman services offer a one-stop solution for all your home repair and maintenance needs. From fixing leaks and repairing drywall to handling electrical and plumbing issues, our skilled professionals are ready to tackle a variety of tasks. We prioritize efficiency, quality craftsmanship, and timely completion to ensure your home is well-maintained and functional. Let us take care of the details, so you can enjoy a hassle-free living space. Contact us for reliable and comprehensive handyman services tailored to your specific requirements.

    ##  About Us 

    #####  Learn more about what we do 

    With 25 plus years of extensive experience, we specialize in various facets of residential construction, and handyman services. Our primary focus lies in the small job market, where we define handyman services as the versatility to provide a range of skills and the capability to tackle smaller tasks. As your dedicated resource, we aim to be your go-to solution for all your home projects, offering expertise and reliability for every job, no jobs too small.  

    ##  Trust 

    We understand the importance of trust when it comes to your home. With a reputation built on reliability and professionalism, we prioritize your confidence in our work. Our team is dedicated to providing trustworthy services for all your home repair and improvement needs. Choose 425 Handyman Services for a reliable partner in maintaining and enhancing your home.

    ##  Need Help 

    Dealing with a home emergency? Whether it's a pressing issue that needs immediate resolution or any other concern, we're here to assist you. Contact us promptly to check our availability and get the help you require.

     Contact Us 

    ###  Service Area 

    #####  Location 

    King County, WA

    #####  Contact 

    Email: Info@425handymanservices.com

    #####  Hours 

    Monday-Friday: 8:00AM - 4:00PM  

     (425)242-8631 

     Info@425handymanservices.com 

     Licensed Bonded and Insured 
    """
    
    # Initialize service
    service = ContractorService()
    
    print("🔍 DEBUGGING VALIDATION FOR 425 HANDYMAN SERVICES LLC")
    print("=" * 60)
    
    print(f"📋 Contractor Data:")
    print(f"   Business Name: {contractor.business_name}")
    print(f"   License: {contractor.contractor_license_number}")
    print(f"   Phone: {contractor.phone_number}")
    print(f"   Address: {contractor.address1}, {contractor.city}, {contractor.state} {contractor.zip}")
    print(f"   Principal: {contractor.primary_principal_name}")
    print(f"   Website: {contractor.website_url}")
    
    print(f"\n🌐 Website Content Preview:")
    print(f"   Length: {len(website_content)} characters")
    print(f"   Phone in content: {'(425)242-8631' in website_content}")
    print(f"   Address in content: {'King County' in website_content}")
    
    print(f"\n🔍 VALIDATION RESULTS:")
    print("-" * 40)
    
    # Test phone matching
    phone_match = service._phone_number_matching(contractor.phone_number, website_content)
    print(f"📞 Phone Match: {phone_match}")
    print(f"   Database phone: '{contractor.phone_number}'")
    print(f"   Website phone: '(425)242-8631'")
    
    # Test address matching
    address_match = service._address_matching(contractor.address1, website_content)
    print(f"📍 Address Match: {address_match}")
    print(f"   Database address: '{contractor.address1}'")
    print(f"   Website location: 'King County, WA'")
    
    # Test license matching
    license_match = service._license_matching(contractor.contractor_license_number, website_content)
    print(f"📜 License Match: {license_match}")
    print(f"   Database license: '{contractor.contractor_license_number}'")
    
    # Test principal name matching
    principal_match = service._principal_name_matching(contractor.primary_principal_name, website_content)
    print(f"👤 Principal Match: {principal_match}")
    print(f"   Database principal: '{contractor.primary_principal_name}'")
    
    # Test business name matching
    business_name_match = service._advanced_business_name_matching(contractor.business_name, website_content)
    print(f"🏢 Business Name Match: {business_name_match}")
    print(f"   Database name: '{contractor.business_name}'")
    print(f"   Website name: '425 Handyman Services'")
    
    # Test domain matching
    domain_match = service._domain_business_name_matching(contractor.business_name, contractor.website_url)
    print(f"🌐 Domain Match: {domain_match}")
    print(f"   Domain: 'www.425handymanservices.com'")
    
    print(f"\n📊 SUMMARY:")
    print("-" * 40)
    print(f"   Phone Match: {'✅' if phone_match else '❌'}")
    print(f"   Address Match: {'✅' if address_match else '❌'}")
    print(f"   License Match: {'✅' if license_match else '❌'}")
    print(f"   Principal Match: {'✅' if principal_match else '❌'}")
    print(f"   Business Name Match: {'✅' if business_name_match else '❌'}")
    print(f"   Domain Match: {'✅' if domain_match > 0 else '❌'}")
    
    # Calculate confidence
    validation_results = {
        'business_name_match': business_name_match > 0.5,
        'keyword_business_name_match': business_name_match > 0.2,
        'license_match': license_match,
        'phone_match': phone_match,
        'address_match': address_match,
        'principal_name_match': principal_match,
        'domain_match_score': domain_match
    }
    
    confidence = service._calculate_validation_confidence(validation_results)
    print(f"\n🎯 CALCULATED CONFIDENCE: {confidence:.2f}")
    
    await db_pool.close()

if __name__ == "__main__":
    asyncio.run(debug_validation()) 