<?xml version="1.0" encoding="UTF-8"?>
<mets:mets xmlns:mets="http://www.loc.gov/METS/"
 xmlns:mods="http://www.loc.gov/mods/v3"
 xmlns:rts="http://cosimo.stanford.edu/sdr/metsrights/"
 xmlns:mix="http://www.loc.gov/mix/v10"
 xmlns:xlink="http://www.w3.org/1999/xlink"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:schemaLocation=
"http://www.loc.gov/METS/
 http://www.loc.gov/standards/mets/mets.xsd
 http://cosimo.stanford.edu/sdr/metsrights/
 http://cosimo.stanford.edu/sdr/metsrights.xsd
 http://www.loc.gov/mods/v3
 http://www.loc.gov/standards/mods/v3/mods-3-2.xsd
 http://www.loc.gov/mix/v10
 http://www.loc.gov/standards/mix/mix10/mix10.xsd"
 OBJID="ddr-densho-15-110"
 LABEL="Storefront of Valley Seed Company"
 PROFILE="http://www.loc.gov/mets/profiles/00000013.xml">

 
<mets:metsHdr CREATEDATE="2005-07-13T11:24:07" LASTMODDATE="2008-03-12T09:46:02">
  <mets:agent ROLE="CREATOR" TYPE="ORGANIZATION">
   <mets:name>Densho</mets:name>
  </mets:agent>
</mets:metsHdr>

<!-- This section is a reference to the element in the parent collection EAD doc. Necessary? Maybe use a dc:relation reference instead? -->
<mets:dmdSec ID="DMR2">
<mets:mdRef xlink:href="http://www.oac.cdlib.org/findaid/ark:/13030/kt8h4nd0m3"
 XPTR="xpointer(id('cc409'))"
 LOCTYPE="URL"
 MDTYPE="EAD"
 LABEL="Drawings of Indians and California scenery" />
</mets:dmdSec>

<!-- Main descriptive section. Contains MODS data. -->

<mets:dmdSec ID="DM1">
 <mets:mdWrap MDTYPE="MODS" LABEL="Storefront of Valley Seed Company">
  <mets:xmlData>
    <mods:mods>
	
	
	<!-- densho:id -->
    <mods:identifier displayLabel="Densho ID" type="local">denshopd-p242-00024</mods:identifier>

	<!-- densho:title -->
     <mods:titleInfo>
      <mods:title>Issei man in front of his store</mods:title>
     </mods:titleInfo>

	<!-- densho:Creator -->
     <mods:name type="organization" authority="naf">
      <mods:namePart>Anderson Photo Service</mods:namePart>
      <mods:role>
       <mods:roleTerm type="text" authority="marcrelator">Artist</mods:roleTerm>
      </mods:role>
     </mods:name>

	<!-- densho:objectformat -->
     <mods:typeOfResource>Still Image</mods:typeOfResource>

	<!-- densho:genre -->
     <mods:genre authority="densho">Photographs</mods:genre>


    <!-- densho:datecreated -->
 	<mods:originInfo>
      <mods:dateCreated>1851</mods:dateCreated>
      <mods:dateCreated encoding="iso8601" point="start">1851</mods:dateCreated>
     </mods:originInfo>

	<!-- densho:language -->
     <mods:language>
      <mods:languageTerm type="code" authority="iso639-3">eng</mods:languageTerm>
     </mods:language>

	<!-- densho:Physical Dimensions -->
     <mods:physicalDescription>
     <mods:extent>8W x 10H</mods:extent>
     </mods:physicalDescription>

	<!-- densho:Description -->
	<mods:abstract>Caption by Ike Hatchimonji: "Kunezo Hatchimonji in front of his seed store in El Monte, Calif."</mods:abstract>
	
	<!-- densho:topic Q:can we link to external controlled term with xlink? -->
     <mods:subject>
      <mods:topic xlink:href="http://id.densho.org/cv/topics/8">Small Business [8]</mods:topic>
     </mods:subject>
	<!-- densho:geography -->
     <mods:subject>
      <mods:geographic>El Monte, California</mods:geographic>
     </mods:subject>
	
	<!-- densho:facility -->
     <mods:subject>
      <mods:geographic xlink:href="http://id.densho.org/cv/facility/27">Tule Lake</mods:geographic>
     </mods:subject>

	<!-- densho:People/Organizations -->
	<mods:subject>
     <mods:name type="personal" authority="naf">
      <mods:namePart>Hatchimonji, Kumezo</mods:namePart>
     </mods:name>
     <mods:name type="organization" authority="naf">
      <mods:namePart>Valley Seed Co.</mods:namePart>
     </mods:name>
	</mods:subject>
	
	<!-- densho:chronology -->
	<mods:subject>
		<mods:temporal>1934-1942</mods:temporal>
	</mods:subject>
	
	<!-- densho:collection ?? -->
     <mods:relatedItem displayLabel="Metacollection" type="host">
      <mods:titleInfo>
       <mods:title>Hatchimonji Collection</mods:title>
      </mods:titleInfo>
      <mods:identifier type="uri">http://calcultures.cdlib.org/</mods:identifier>
      <mods:identifier type="local search">hb500007cn</mods:identifier>
     </mods:relatedItem>
     <mods:relatedItem displayLabel="Collection" type="host">
      <mods:titleInfo>
       <mods:title>Drawings of Indians and California scenery</mods:title>
      </mods:titleInfo>
      <mods:identifier type="local">BANC PIC 1980.022--A</mods:identifier>
      <mods:identifier type="uri">http://www.oac.cdlib.org/findaid/ark:/13030/kt8h4nd0m3</mods:identifier>
     </mods:relatedItem>

	<!-- densho: -->
     <mods:location>
      <mods:physicalLocation>The Bancroft Library, University of California, Berkeley, Berkeley, CA 94720-6000, Phone: (510) 642-6481, Fax: (510) 642-7589, Email: bancref@library.berkeley.edu, URL: http://bancroft.berkeley.edu/</mods:physicalLocation>
     </mods:location>

    </mods:mods>
  </mets:xmlData>
 </mets:mdWrap>
</mets:dmdSec>

<mets:amdSec>

<!-- each techMD contains MIX info for a binary associated with the object. techMD@ID is referenced in fileSec/file to link the extended technical metadata to its binary. This is also where PREMIS events would go -->

 <mets:techMD ID="ADM1">
  <mets:mdWrap MDTYPE="NISOIMG">
   <mets:xmlData>
    <mix:mix>

     <mix:BasicDigitalObjectInformation>
       <mix:FormatDesignation>
         <mix:formatName>image/tiff</mix:formatName>
       </mix:FormatDesignation>
       <mix:Compression>
         <mix:compressionScheme>Uncompressed</mix:compressionScheme>
       </mix:Compression>
     </mix:BasicDigitalObjectInformation>
     <mix:BasicImageInformation>
       <mix:BasicImageCharacteristics> 
         <mix:PhotometricInterpretation>
           <mix:colorSpace>RGB</mix:colorSpace>
           <mix:ColorProfile>
             <mix:IccProfile>
               <mix:iccProfileName>E836G18_01_DIL</mix:iccProfileName>
             </mix:IccProfile>
           </mix:ColorProfile>
         </mix:PhotometricInterpretation>
       </mix:BasicImageCharacteristics>
     </mix:BasicImageInformation>
     <mix:ImageCaptureMetadata>
       <mix:GeneralCaptureInformation>
         <mix:imageProducer>DIL/U.C. Berkeley Library</mix:imageProducer>
         <mix:captureDevice>reflection print scanner</mix:captureDevice>
       </mix:GeneralCaptureInformation>
       <mix:ScannerCapture>
         <mix:scannerManufacturer>Epson</mix:scannerManufacturer>
         <mix:ScannerModel>
           <mix:scannerModelName>836xl</mix:scannerModelName>
           <mix:scannerModelSerialNo>B05401003MG9601009</mix:scannerModelSerialNo>
         </mix:ScannerModel>
       </mix:ScannerCapture>
     </mix:ImageCaptureMetadata>
     <mix:ImageAssessmentMetadata>
       <mix:SpatialMetrics>
         <mix:samplingFrequencyUnit>2</mix:samplingFrequencyUnit>
         <mix:xSamplingFrequency>
           <mix:numerator>600</mix:numerator>
         </mix:xSamplingFrequency>
         <mix:ySamplingFrequency>
           <mix:numerator>600</mix:numerator>
         </mix:ySamplingFrequency>
       </mix:SpatialMetrics>
       <mix:ImageColorEncoding>
         <mix:bitsPerSample>
           <mix:bitsPerSampleValue>8,8,8</mix:bitsPerSampleValue>
           <mix:bitsPerSampleUnit>integer</mix:bitsPerSampleUnit>
         </mix:bitsPerSample>
         <mix:samplesPerPixel>3</mix:samplesPerPixel>
       </mix:ImageColorEncoding>
     </mix:ImageAssessmentMetadata>

    </mix:mix>
   </mets:xmlData>
  </mets:mdWrap>
 </mets:techMD>

 <mets:techMD ID="ADM2">
  <mets:mdWrap MDTYPE="NISOIMG">
   <mets:xmlData>
    <mix:mix>

     <mix:BasicDigitalObjectInformation>
       <mix:FormatDesignation>
         <mix:formatName>image/gif</mix:formatName> 
       </mix:FormatDesignation>
       <mix:Compression>
         <mix:compressionScheme>LZW</mix:compressionScheme>
       </mix:Compression>
     </mix:BasicDigitalObjectInformation>
     <mix:BasicImageInformation>
       <mix:BasicImageCharacteristics>
         <mix:PhotometricInterpretation>
           <mix:colorSpace>RGB</mix:colorSpace>
         </mix:PhotometricInterpretation>
       </mix:BasicImageCharacteristics>
     </mix:BasicImageInformation>
     <mix:ImageAssessmentMetadata>
       <mix:SpatialMetrics>
         <mix:samplingFrequencyUnit>2</mix:samplingFrequencyUnit>
         <mix:xSamplingFrequency>
           <mix:numerator>13</mix:numerator>
         </mix:xSamplingFrequency>
         <mix:ySamplingFrequency>
           <mix:numerator>13</mix:numerator>
         </mix:ySamplingFrequency>
       </mix:SpatialMetrics>
       <mix:ImageColorEncoding>
         <mix:bitsPerSample>
           <mix:bitsPerSampleValue>8</mix:bitsPerSampleValue>
           <mix:bitsPerSampleUnit>integer</mix:bitsPerSampleUnit>
         </mix:bitsPerSample>
         <mix:samplesPerPixel>1</mix:samplesPerPixel>
       </mix:ImageColorEncoding>
     </mix:ImageAssessmentMetadata>
     <mix:ChangeHistory>
       <mix:ImageProcessing>
           <mix:processingAgency>DIL/U.C. Berkeley Library</mix:processingAgency>
           <mix:ProcessingSoftware>
             <mix:processingSoftwareName>Photoshop</mix:processingSoftwareName>
           </mix:ProcessingSoftware>
       </mix:ImageProcessing>
     </mix:ChangeHistory>

    </mix:mix>
   </mets:xmlData>
  </mets:mdWrap>
 </mets:techMD>

 <mets:techMD ID="ADM3">
  <mets:mdWrap MDTYPE="NISOIMG">
   <mets:xmlData>
    <mix:mix>

     <mix:BasicDigitalObjectInformation>
       <mix:FormatDesignation>
         <mix:formatName>image/jpeg</mix:formatName> 
       </mix:FormatDesignation>
       <mix:Compression>
         <mix:compressionScheme>JPEG Baseline Sequential</mix:compressionScheme>
       </mix:Compression>
     </mix:BasicDigitalObjectInformation>
     <mix:BasicImageInformation>
       <mix:BasicImageCharacteristics>
         <mix:PhotometricInterpretation>
           <mix:colorSpace>RGB</mix:colorSpace>
         </mix:PhotometricInterpretation>
       </mix:BasicImageCharacteristics>
     </mix:BasicImageInformation>
     <mix:ImageAssessmentMetadata>
       <mix:SpatialMetrics>
         <mix:samplingFrequencyUnit>2</mix:samplingFrequencyUnit>
         <mix:xSamplingFrequency>
           <mix:numerator>82</mix:numerator>
         </mix:xSamplingFrequency>
         <mix:ySamplingFrequency>
           <mix:numerator>82</mix:numerator>
         </mix:ySamplingFrequency>
       </mix:SpatialMetrics>
       <mix:ImageColorEncoding>
         <mix:bitsPerSample>
           <mix:bitsPerSampleValue>8,8,8</mix:bitsPerSampleValue>
           <mix:bitsPerSampleUnit>integer</mix:bitsPerSampleUnit>
         </mix:bitsPerSample>
         <mix:samplesPerPixel>3</mix:samplesPerPixel>
       </mix:ImageColorEncoding>
     </mix:ImageAssessmentMetadata>
     <mix:ChangeHistory>
       <mix:ImageProcessing>
           <mix:processingAgency>DIL/U.C. Berkeley Library</mix:processingAgency>
           <mix:ProcessingSoftware>
             <mix:processingSoftwareName>Photoshop</mix:processingSoftwareName>
           </mix:ProcessingSoftware>
       </mix:ImageProcessing>
     </mix:ChangeHistory>

    </mix:mix>
   </mets:xmlData>
  </mets:mdWrap>
 </mets:techMD>

 <mets:techMD ID="ADM4">
  <mets:mdWrap MDTYPE="NISOIMG">
   <mets:xmlData>
    <mix:mix>

     <mix:BasicDigitalObjectInformation>
       <mix:FormatDesignation>
         <mix:formatName>image/jpeg</mix:formatName> 
       </mix:FormatDesignation>
       <mix:Compression>
         <mix:compressionScheme>JPEG Baseline Sequential</mix:compressionScheme>
       </mix:Compression>
     </mix:BasicDigitalObjectInformation>
     <mix:BasicImageInformation>
       <mix:BasicImageCharacteristics>
         <mix:PhotometricInterpretation>
           <mix:colorSpace>RGB</mix:colorSpace>
         </mix:PhotometricInterpretation>
       </mix:BasicImageCharacteristics>
     </mix:BasicImageInformation>
     <mix:ImageAssessmentMetadata>
       <mix:SpatialMetrics>
         <mix:samplingFrequencyUnit>2</mix:samplingFrequencyUnit>
         <mix:xSamplingFrequency>
           <mix:numerator>165</mix:numerator>
         </mix:xSamplingFrequency>
         <mix:ySamplingFrequency>
           <mix:numerator>165</mix:numerator>
         </mix:ySamplingFrequency>
       </mix:SpatialMetrics>
       <mix:ImageColorEncoding>
         <mix:bitsPerSample>
           <mix:bitsPerSampleValue>8,8,8</mix:bitsPerSampleValue>
           <mix:bitsPerSampleUnit>integer</mix:bitsPerSampleUnit>
         </mix:bitsPerSample>
         <mix:samplesPerPixel>3</mix:samplesPerPixel>
       </mix:ImageColorEncoding>
     </mix:ImageAssessmentMetadata>
     <mix:ChangeHistory>
       <mix:ImageProcessing>
           <mix:processingAgency>DIL/U.C. Berkeley Library</mix:processingAgency>
           <mix:ProcessingSoftware>
             <mix:processingSoftwareName>Photoshop</mix:processingSoftwareName>
           </mix:ProcessingSoftware>
       </mix:ImageProcessing>
     </mix:ChangeHistory>

    </mix:mix>
   </mets:xmlData>
  </mets:mdWrap>
 </mets:techMD>

 <mets:techMD ID="ADM5">
  <mets:mdWrap MDTYPE="NISOIMG">
   <mets:xmlData>
    <mix:mix>
     <mix:BasicDigitalObjectInformation>
       <mix:ObjectIdentifier>
         <mix:objectIdentifierType>ark</mix:objectIdentifierType>
         <mix:objectIdentifierValue>ark:/28722/bk0001j1m10</mix:objectIdentifierValue>
       </mix:ObjectIdentifier>
     </mix:BasicDigitalObjectInformation>
     <mix:BasicImageInformation>
       <mix:BasicImageCharacteristics>
         <mix:imageWidth>3248</mix:imageWidth>
         <mix:imageHeight>5470</mix:imageHeight>
       </mix:BasicImageCharacteristics>
     </mix:BasicImageInformation>
     <mix:ImageCaptureMetadata>
       <mix:SourceInformation>
         <mix:sourceType>still image</mix:sourceType>
         <mix:SourceID>
           <mix:sourceIDType>Local identifier</mix:sourceIDType>
           <mix:sourceIDValue>BANC PIC 1980.022:01--A</mix:sourceIDValue>
         </mix:SourceID>
       </mix:SourceInformation>
       <mix:GeneralCaptureInformation>
         <mix:dateTimeCreated>2003-01-22</mix:dateTimeCreated>
       </mix:GeneralCaptureInformation>
     </mix:ImageCaptureMetadata>
    </mix:mix>
   </mets:xmlData>
  </mets:mdWrap>
 </mets:techMD>

 <mets:techMD ID="ADM6">
  <mets:mdWrap MDTYPE="NISOIMG">
   <mets:xmlData>
    <mix:mix>
     <mix:BasicDigitalObjectInformation>
       <mix:ObjectIdentifier>
         <mix:objectIdentifierType>ark</mix:objectIdentifierType>
         <mix:objectIdentifierValue>ark:/28722/bk0001j1m2j</mix:objectIdentifierValue>
       </mix:ObjectIdentifier>
     </mix:BasicDigitalObjectInformation>
     <mix:BasicImageInformation>
       <mix:BasicImageCharacteristics>
         <mix:imageWidth>73</mix:imageWidth>
         <mix:imageHeight>125</mix:imageHeight>
       </mix:BasicImageCharacteristics>
     </mix:BasicImageInformation>
     <mix:ChangeHistory>
       <mix:ImageProcessing>
         <mix:dateTimeProcessed>2003-01-22</mix:dateTimeProcessed>
         <mix:sourceData>http://nma.berkeley.edu/ark:/28722/bk0001j1m10</mix:sourceData>
       </mix:ImageProcessing>
     </mix:ChangeHistory>
    </mix:mix>
   </mets:xmlData>
  </mets:mdWrap>
 </mets:techMD>

 <mets:techMD ID="ADM7">
  <mets:mdWrap MDTYPE="NISOIMG">
   <mets:xmlData>
    <mix:mix>
     <mix:BasicDigitalObjectInformation>
       <mix:ObjectIdentifier>
         <mix:objectIdentifierType>ark</mix:objectIdentifierType>
         <mix:objectIdentifierValue>ark:/28722/bk0001j1m33</mix:objectIdentifierValue>
       </mix:ObjectIdentifier>
     </mix:BasicDigitalObjectInformation>
     <mix:BasicImageInformation>
       <mix:BasicImageCharacteristics>
         <mix:imageWidth>445</mix:imageWidth>
         <mix:imageHeight>750</mix:imageHeight>
       </mix:BasicImageCharacteristics>
     </mix:BasicImageInformation>
     <mix:ChangeHistory>
       <mix:ImageProcessing>
         <mix:dateTimeProcessed>2003-01-22</mix:dateTimeProcessed>
         <mix:sourceData>http://nma.berkeley.edu/ark:/28722/bk0001j1m10</mix:sourceData>
       </mix:ImageProcessing>
     </mix:ChangeHistory>
    </mix:mix>
   </mets:xmlData>
  </mets:mdWrap>
 </mets:techMD>

 <mets:techMD ID="ADM8">
  <mets:mdWrap MDTYPE="NISOIMG">
   <mets:xmlData>
    <mix:mix>
     <mix:BasicDigitalObjectInformation>
       <mix:ObjectIdentifier>
         <mix:objectIdentifierType>ark</mix:objectIdentifierType>
         <mix:objectIdentifierValue>ark:/28722/bk0001j1m4n</mix:objectIdentifierValue>
       </mix:ObjectIdentifier>
     </mix:BasicDigitalObjectInformation>
     <mix:BasicImageInformation>
       <mix:BasicImageCharacteristics>
         <mix:imageWidth>893</mix:imageWidth>
         <mix:imageHeight>1500</mix:imageHeight>
       </mix:BasicImageCharacteristics>
     </mix:BasicImageInformation>
     <mix:ChangeHistory>
       <mix:ImageProcessing>
         <mix:dateTimeProcessed>2003-01-22</mix:dateTimeProcessed>
         <mix:sourceData>http://nma.berkeley.edu/ark:/28722/bk0001j1m10</mix:sourceData>
       </mix:ImageProcessing>
     </mix:ChangeHistory>
    </mix:mix>
   </mets:xmlData>
  </mets:mdWrap>
 </mets:techMD>

<!-- refers to rights -->
 <mets:rightsMD ID="RMD1">
  <mets:mdWrap MDTYPE="OTHER" OTHERMDTYPE="METSRights">
   <mets:xmlData>
    <rts:RightsDeclarationMD RIGHTSCATEGORY="OTHER" OTHERCATEGORYTYPE="UNKNOWN">
     <rts:RightsHolder>
      <rts:RightsHolderComments>All requests to reproduce, publish, quote from, or otherwise use collection materials must be submitted in writing to the Head of Access Services, The Bancroft Library, University of California, Berkeley 94720-6000. Consent is given on behalf of The Bancroft Library as the owner of the physical items and does not constitute permission from the copyright owner.  Such permission must be obtained from the copyright owner.   See: http://bancroft.berkeley.edu/reference/permissions.html</rts:RightsHolderComments>
     </rts:RightsHolder>
     <rts:Context CONTEXTCLASS="GENERAL PUBLIC">
      <rts:Constraints>
       <rts:ConstraintDescription>Copyright status unknown. Some materials in these collections may be protected by the U.S. Copyright Law (Title 17, U.X.C.). In addition, the reproduction of some materials may be restricted by terms of University of California gift or purchase agreements, donor restrictions, privacy and publicity rights, licensing and trademarks. Transmission or reproduction of materials protected by copyright beyond that allowed by fair use requires the written permission of copyright owners.  Works not in the public domain cannot be commercially exploited without permission of the copyright owner. Responsibility for any use rests exclusively with the user.</rts:ConstraintDescription>
      </rts:Constraints>
     </rts:Context>
    </rts:RightsDeclarationMD>

   </mets:xmlData>
  </mets:mdWrap>
 </mets:rightsMD>

</mets:amdSec>

<mets:fileSec>

 <mets:fileGrp USE="image/master">
   <mets:file ID="FID1" MIMETYPE="image/tiff" SEQ="1" CREATED="2003-01-22T00:00:00.0" ADMID="ADM1 ADM5" GROUPID="GID1">
	<!-- -->
    <mets:FLocat xlink:href="http://nma.berkeley.edu/ark:/28722/bk0001j1m10" LOCTYPE="URL"/>
   </mets:file>
 </mets:fileGrp>

 <mets:fileGrp USE="image/thumbnail">
   <mets:file ID="FID2" MIMETYPE="image/gif" SEQ="1" CREATED="2003-01-22T00:00:00.0" ADMID="ADM2 ADM6" GROUPID="GID1">
    <mets:FLocat xlink:href="http://nma.berkeley.edu/ark:/28722/bk0001j1m2j" LOCTYPE="URL"/>
   </mets:file>
 </mets:fileGrp>

 <mets:fileGrp USE="image/reference">
   <mets:file ID="FID3" MIMETYPE="image/jpeg" SEQ="1" CREATED="2003-01-22T00:00:00.0" ADMID="ADM3 ADM7" GROUPID="GID1">
    <mets:FLocat xlink:href="http://nma.berkeley.edu/ark:/28722/bk0001j1m33" LOCTYPE="URL"/>
   </mets:file>
 </mets:fileGrp>

 <mets:fileGrp USE="image/reference">
   <mets:file ID="FID4" MIMETYPE="image/jpeg" SEQ="1" CREATED="2003-01-22T00:00:00.0" ADMID="ADM4 ADM8" GROUPID="GID1">
    <mets:FLocat xlink:href="http://nma.berkeley.edu/ark:/28722/bk0001j1m4n" LOCTYPE="URL"/>
   </mets:file>
 </mets:fileGrp>

</mets:fileSec>

<mets:structMap>
  <mets:div TYPE="still image" LABEL="S.P. [Simmon Pe??a] Storms, Interpreter [&amp;c], Indian agency - near Grass Valley, California, 1851" ADMID="RMD1" DMDID="DMR1 DMR2 DM1">
    <mets:fptr FILEID="FID1"/>
    <mets:fptr FILEID="FID2"/>
    <mets:fptr FILEID="FID3"/>
    <mets:fptr FILEID="FID4"/>
  </mets:div>
</mets:structMap>

</mets:mets>
