#!/usr/bin/env python3
"""
Test AI business name mismatch detection
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.services.contractor_service import ContractorService

async def test_ai_business_mismatch():
    """Test AI detection of business name mismatches"""
    
    service = ContractorService()
    
    # Test case: A TEAM PAINTING vs Runland Painting website
    business_name = "A TEAM PAINTING"
    website_content = """
    Runland Painting Tacoma | Painting Puyallup | WA 98374 | Best Interior Painting Exterior Painting| Pressure Washing, Concrete Coating| Wallpaper Removal 

    Runland Painting Tacoma | Painting Puyallup | WA 98374 | Best Interior Painting Exterior Painting| Pressure Washing, Concrete Coating| Wallpaper Removal 

    * Careers Schedule Estimate 253.212.2679  
    253.886.3668

    * Home
    * About  
       * About Us  
       * Photo Gallery  
       * Online Job Application  
       * Testimonials
    * Residential Services  
       * Interior Painting  
       * Exterior Painting  
       * Pressure Washing  
       * Popcorn Ceiling Removal and Drywall Repair  
       * Cabinet Painting  
       * Trim Work  
       * Siding Repair  
       * Gutters and Gutter Guards
    * Commercial Services  
       * Superior Commercial Painting  
       * Pressure Washing  
       * Popcorn Ceiling Removal and Drywall Repair  
       * Cabinet Painting  
       * Trim Work  
       * Siding Repair
    * Gutters
    * Schedule Estimate
    * Cities Served  
       * Puyallup  
       * Auburn  
       * Bonney Lake  
       * Sumner  
       * Lake Tapps  
       * Milton  
       * Pacific  
       * Tacoma  
       * Gig Harbor  
       * Federal Way  
       * Enumclaw  
       * Maple Valley  
       * Covington
    * Special Offers
    * Contact  
       * Contact Us  
       * Schedule Estimate  
       * Online Job Application  
       * Write A Review Painting  
       * Write a Review Gutters

    We're Hiring!

    ##   
     Residential Services
      
      
    # Interior Painting

    Divider  
      
    Tacoma Painting | Painting Tacoma Residential Interior Painting Runland Painting Tacoma | Painting Puyallup | WA 98374 | Best Interior Painting Exterior Painting| Pressure Washing, Concrete Coating| Wallpaper Removal 

    ### Trusted Residential Painting

    Runland Painting has a team of trusted, experienced painting contractors dedicated to delivering superior work. We handle both interior and exterior residential painting.   
      
    Our hand-picked painting contractors uphold the highest standards. We use Sherwin Williams products for everything we do, ensuring the best results.   
      
    Because we adhere to such strict standards, we are able to offer a 2-year warranty.  
      
    Tacoma Painting | Painting Tacoma  Sherwin Williams   

    ### Turn your house into a home with residential painting from Runland!

     We work with you to create the exact look and feel you want. Revitalize a single room or your entire home and love where you live.   
      
    Schedule Estimate   
      
      
    #### Residential Services

    * Interior Painting
    * Exterior Painting
    * Pressure Washing
    * Popcorn Ceiling Removal and Drywall Repair
    * Cabinet Painting
    * Trim Work
    * Siding Repair
    * Gutters and Gutter Guards

      
    Runland Painting 

    * Schedule Estimate
      
      
    ## What makes us different?

    Licensed, Bonded & Insured  

    ### Licensed, Bonded & Insured

    We understand that custom painting isn't just about quality service—it's about trust and communication. 

    Experienced Employees  

    ### Experienced Employees

    All our painters and gutter installers are experienced and well-trained. 

    Two Year Warranty  

    ### Two Year Warranty

    We are proud of our long list of happy customers, and we provide a 2-year warranty on our services. 

    Only Top Quality Products  

    ### Only Top Quality Products

    We only use Sherwin Williams products to ensure the highest quality paint, sealant, and caulking. 

    Locally & Family Owned  

    ### Locally & Family Owned

    Runland Painting is locally owned and family operated, so we can work with your busy schedule. 

      
    Testimonials  
    What Our Happy Customers Say  
      
     We hired Runland and worked with Jorge and his crew. They were so kind, listened to our wants when it came to texture, paint and general aesthetic, and they truly did an exemplary job. Communication was great the entire time, and once the job wrapped up we did a detailed walk through. Everything was pristine, but Jorge still reassured me that if I found anything that wasn't to my satisfaction, I could call him and they would return to would make it right. I would happily hire these guys again. 

     Kristen K. 

     We recently had our home's interior painted by Runland Painting and Renovations. We couldn't be more impressed with the quality of work. This wasn't just a straightforward paint job—all the doors and trim hadn't been painted in 20 years and we needed skilled painters who had attention to detail and could handle any necessary repairs. Also our home had some settling issues that left noticeable ceiling cracks. The crew took the time to repair them flawlessly before even starting on the paint. The project manager, Jorge did a thorough walk through before the crew started and after the work was completed to ensure all details were reviewed and the project was completed properly. It's refreshing to have a company like Runland Painting who truly cares about the quality of their work and does exactly what they said they would do. We're so happy we chose them and now our home looks brand new inside! 

     Laurie S. 

     Runland Painting is the most professional painting company we have used to date. They came, worked hard, cleaned up and finished painting the exterior of our home before we could blink an eye. Fabulous crew, considerate, hard workers, superior job. Now when I come home at the end of my day I stop in my driveway and just look at the beautiful job they did painting my home and it puts a huge smile on my face. Thank you John for having such a great crew, they are what made this experience top notch.

     Andrea C. on Google 

     Runland Painting did the interior of our home. After receiving 3 estimates we decided to go with them because of their reputation. They were the highest estimate but we are so happy we choose them. The staff and the owner were wonderful to work with. Our home was treated with respect and the paint job looks amazing. We recommend Runland Painting to anyone needing a painter!

     James D. on Google 

     We just had the inside of our house painted and also our kitchen cabinets by Runland Painting. I am so pleased with the work that John and his crew did! John was so knowledgeable and helpful when it came to choosing the right colors and giving me ideas. All of my questions/concerns were always answered quickly. John and his crew were very meticulous and detail oriented, and I am a very picky person. Everything looks wonderful, and it feels like I have a brand new house! Thank you! 

     Judy M. on Google 

     Runland Painting just completed a mud, tape, prime, texture, and paint job on a bedroom/bathroom remodel we were doing for our parents. The crew did a better job on our drywall then drywall contractors we've used for other projects in the past. Everything looked amazing! Communication is great; straight and to the point. Very professional and timely company. 

     Michelle E. on Google 

     John is quick to respond and answer any questions you have. The Runland painting crew we're on time and more importantly kind and respectful during their time in our home. Both my wife and I love the new look of our interior, almost feels like a totally new home. Thank you Runland painting. 

     Chad H. on Google 

     I solicited 7 bids for my getting my house and garage repainted. Far and away, Runland Painting had the most professional bid and a reasonable price. I was very impressed by their technical expertise and how they explained it to a non-expert like myself. The actual job turned out great. John responded promptly to all my concerns and his team worked extremely hard. I would recommend them to anyone looking for exterior paint work. 

     John O. on Google 

     We hired Runland after hearing great things about them. Today, our house looks wonderful and my husband and I love the finished product. John's prep team was incredible they paved the way for John's paint team. Mason was the lead for our paint team. He is a young kid but he did a wonderful job managing his team. The end of the job required some touch up. Mason and one of the other painters, Aaron came back and worked hard to ensure everything was finished to our satisfaction. I would definitely recommend Runland Painting to anyone. 

     Melynda K. on Google 

     John Runland was professional and accommodating to the particular needs of our project. The crews were efficient, safe, and courteous. Their expert professionalism shows in the prep work, painting, and clean up. They were onsite when they were scheduled to be there and communication with us was excellent. I would recommend Runland Painting to any friend or family member. Well Done! 

     William V. on Google 

     I used Runland Painting to paint the exterior of my home. I am very pleased with the job they did. John was very easy to work with and very responsive. He always answered my questions and responded to any concerns that I had quickly. The crew always arrived on time and when they were scheduled. They communicated very well and always let me know what they would be working on. It was a big job and well executed. I have had so many neighbors come by and comment on how beautiful it looks. I couldn't be happier with Runland Painting and I would definitely recommend them. They also completed my job earlier than planned. Thank you John! 

     Chalene D. on Google 
      
      
    Read More   
      
    Review  
    What Our Customers Say  
      
     We hired Runland and worked with Jorge and his crew. They were so kind, listened to our wants when it came to texture, paint and general aesthetic, and they truly did an exemplary job. Communication was great the entire time, and once the job wrapped up we did a detailed walk through. Everything was pristine, but Jorge still reassured me that if I found anything that wasn't to my satisfaction, I could call him and they would return to would make it right. I would happily hire these guys again. 

     Kristen K. 

     We recently had our home's interior painted by Runland Painting and Renovations. We couldn't be more impressed with the quality of work. This wasn't just a straightforward paint job—all the doors and trim hadn't been painted in 20 years and we needed skilled painters who had attention to detail and could handle any necessary repairs. Also our home had some settling issues that left noticeable ceiling cracks. The crew took the time to repair them flawlessly before even starting on the paint. The project manager, Jorge did a thorough walk through before the crew started and after the work was completed to ensure all details were reviewed and the project was completed properly. It's refreshing to have a company like Runland Painting who truly cares about the quality of their work and does exactly what they said they would do. We're so happy we chose them and now our home looks brand new inside! 

     Laurie S. 

     Runland Painting is the most professional painting company we have used to date. They came, worked hard, cleaned up and finished painting the exterior of our home before they could blink an eye. Fabulous crew, considerate, hard workers, superior job. Now when I come home at the end of my day I stop in my driveway and just look at the beautiful job they did painting my home and it puts a huge smile on my face. Thank you John for having such a great crew, they are what made this experience top notch.

     Andrea C. on Google 

     Runland Painting did the interior of our home. After receiving 3 estimates we decided to go with them because of their reputation. They were the highest estimate but we are so happy we choose them. The staff and the owner were wonderful to work with. Our home was treated with respect and the paint job looks amazing. We recommend Runland Painting to anyone needing a painter!

     James D. on Google 

     We just had the inside of our house painted and also our kitchen cabinets by Runland Painting. I am so pleased with the work that John and his crew did! John was so knowledgeable and helpful when it came to choosing the right colors and giving me ideas. All of my questions/concerns were always answered quickly. John and his crew were very meticulous and detail oriented, and I am a very picky person. Everything looks wonderful, and it feels like I have a brand new house! Thank you! 

     Judy M. on Google 

     Runland Painting just completed a mud, tape, prime, texture, and paint job on a bedroom/bathroom remodel we were doing for our parents. The crew did a better job on our drywall then drywall contractors we've used for other projects in the past. Everything looked amazing! Communication is great; straight and to the point. Very professional and timely company. 

     Michelle E. on Google 

     John is quick to respond and answer any questions you have. The Runland painting crew we're on time and more importantly kind and respectful during their time in our home. Both my wife and I love the new look of our interior, almost feels like a totally new home. Thank you Runland painting. 

     Chad H. on Google 

     I solicited 7 bids for my getting my house and garage repainted. Far and away, Runland Painting had the most professional bid and a reasonable price. I was very impressed by their technical expertise and how they explained it to a non-expert like myself. The actual job turned out great. John responded promptly to all my concerns and his team worked extremely hard. I would recommend them to anyone looking for exterior paint work. 

     John O. on Google 

     We hired Runland after hearing great things about them. Today, our house looks wonderful and my husband and I love the finished product. John's prep team was incredible they paved the way for John's paint team. Mason was the lead for our paint team. He is a young kid but he did a wonderful job managing his team. The end of the job required some touch up. Mason and one of the other painters, Aaron came back and worked hard to ensure everything was finished to our satisfaction. I would definitely recommend Runland Painting to anyone. 

     Melynda K. on Google 

     John Runland was professional and accommodating to the particular needs of our project. The crews were efficient, safe, and courteous. Their expert professionalism shows in the prep work, painting, and clean up. They were onsite when they were scheduled to be there and communication with us was excellent. I would recommend Runland Painting to any friend or family member. Well Done! 

     William V. on Google 

     I used Runland Painting to paint the exterior of my home. I am very pleased with the job they did. John was very easy to work with and very responsive. He always answered my questions and responded to any concerns that I had quickly. The crew always arrived on time and when they were scheduled. They communicated very well and always let me know what they would be working on. It was a big job and well executed. I have had so many neighbors come by and comment on how beautiful it looks. I couldn't be happier with Runland Painting and I would definitely recommend them. They also completed my job earlier than planned. Thank you John! 

     Chalene D. on Google 
      
      
    ### Runland Painting

     6024 104th St E  
    Puyallup, WA 98373  
     Phone: (253) 212-2679  
      
    ### Contractor's License

     RUNLUP*843BE  
      
    ### Proudly Serving

    * Puyallup
    * Auburn
    * Bonney Lake
    * Sumner
    * Lake Tapps
    * Enumclaw
    * Maple Valley

    * Milton
    * Pacific
    * Tacoma
    * Gig Harbor
    * Federal Way
    * Covington

    ### Write a Review

     The highest compliment we could receive from our customers would be their reviews.   
      
    Rate your experience and write your review. It's easy to do, and you'll be helping other customers to make better-informed decisions.   
      
      
    Write A Review  
      
    ### Residential Services

    * Interior Painting
    * Exterior Painting
    * Pressure Washing
    * Popcorn Ceiling Removal and Drywall Repair
    * Cabinet Painting
    * Trim Work
    * Siding Repair
    * Gutters and Gutter Guards

    ### Commercial Services

    * Superior Commercial Painting
    * Pressure Washing
    * Popcorn Ceiling Removal and Drywall Repair
    * Cabinet Painting
    * Trim Work
    * Siding Repair

      
    © Runland Painting. All rights reserved. | Terms & Condition | Privacy Policy   
      
     *12-month same-as-cash. Loans provided by EnerBank USA (1245 Brickyard Rd. Ste 600, Salt Lake City, UT 84106) on approved credit, for a limited time. Repayment terms vary from 24 to 132 months. Interest waived if repaid in 365 days. 17.25% fixed APR, effective as of 1/1/18, subject to change. Not to be combined with other offers or discounts. Runland Painting. Coupon void if altered.  
      
    * Appt
    """
    
    print("🔍 TESTING AI BUSINESS NAME MISMATCH DETECTION")
    print("=" * 60)
    print(f"Business Name: {business_name}")
    print(f"Website Content: {website_content[:200]}...")
    print()
    
    # Create a mock contractor for testing
    class MockContractor:
        def __init__(self):
            self.business_name = business_name
            self.city = "PUYALLUP"
            self.state = "WA"
            self.contractor_license_number = "TEST123"
            self.phone_number = "(253) 555-1234"
            self.address1 = "123 Test St"
            self.principal_name = "John Doe"
            self.primary_principal_name = "John Doe"
            self.website_url = "https://www.runlandpainting.com/interior-painting/"
            self.website_status = "found"
            self.data_sources = {'crawled_content': website_content}
    
    contractor = MockContractor()
    
    # Test the AI analysis
    try:
        confidence = await service.enhanced_content_analysis(contractor, None)
        print(f"📊 AI Analysis Result:")
        print(f"   - Confidence: {confidence}")
        print(f"   - Expected: Very low confidence (0.0-0.2) due to business name mismatch")
        print(f"   - Result: {'✅ PASS' if confidence <= 0.2 else '❌ FAIL'}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai_business_mismatch()) 