#!/usr/bin/env python
#====================================================================
#    sforcehelper
#--------------------------------------------------------------------
#    A simple python client for the Salesforce SOAP API v22
#    Required since other python clients do not reliably allow access
#    to all custom objects and fields, regardless of the WSDL used.
#
#    Usage: Create new instance of sforcehelper, passing Salesforce API
#           credentials: sfClient = sforcehelper(user, pass, token).
#           Use create, update, delete and query methods to interact
#           with Salesforce data.
#====================================================================
import httplib
from urlparse import urlparse
import xml.dom.minidom
import string

class Error(Exception):
    """Base class for sforcehelper exceptions"""
    pass

class APIError(Error):
    """Exception raised when an error is received from sf api"""
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)
    
class HTTPError(Error):
    """Exception raised when api request returns HTTP error"""
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)
    

class sforcehelper:
    """Class that acts as a client to the Salesforce SOAP API"""
    #================================================================
    # __init__
    #----------------------------------------------------------------
    #    @param sforceUserId: User ID for salesforce environment
    #    @param sforcePassword: Password for salesforce environment
    #    @param sforceUserToken: User Token for salesforce environment
    #    @param isSandbox: Boolean (true for accessing sandbox)
    #================================================================
    def __init__(self,sforceUserId, sforcePassword, sforceUserToken, isSandbox):
        
        self.SF_LOGIN_ENDPOINT = '/services/Soap/u/22/0'
        if (not isSandbox):
            self.SF_LOGIN_SERVER_URL = 'login.salesforce.com'
        else:
            self.SF_LOGIN_SERVER_URL = 'test.salesforce.com'    
        self.SF_API_REQUEST_ENDPOINT = '/services/Soap/c/22.0'
              
        self.sfUserId = sforceUserId
        self.sfPassword = sforcePassword
        self.sfUserToken = sforceUserToken
        
        self.setSfSoapSession() 
    
    #================================================================
    #    Get Session Id
    #----------------------------------------------------------------
    #    @return: Salesforce API session Id
    #================================================================
    def getSessionId(self):
        return self.sfSessionId
    
    #================================================================
    #    Get Server URL
    #----------------------------------------------------------------
    #    @return: Salesforce API server Url
    #================================================================
    def getServerUrl(self):
        return self.sfServerUrl 

    #================================================================
    #    Get Last Response
    #----------------------------------------------------------------
    #    @return: Last response from the API (useful for debugging)
    #================================================================    
    def getLastResponse(self):
        return self.response

    #================================================================
    #    Get Last Payload
    #----------------------------------------------------------------
    #    @return: Last payload sent to the API (useful for debugging)
    #================================================================        
    def getLastPayload(self):
        return self.payload
    
    #================================================================
    #    Set Sf Soap Session
    #----------------------------------------------------------------
    #    Sets Salesforce SOAP API session info
    #================================================================
    def setSfSoapSession(self):
        self.sfSessionId = None
        payload = '''<?xml version="1.0" encoding="utf-8" ?>
                     <env:Envelope xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:env="http://schemas.xmlsoap.org/soap/envelope/">
                         <env:Body>
                             <n1:login xmlns:n1="urn:partner.soap.sforce.com">
                                 <n1:username>%s</n1:username>
                                 <n1:password>%s%s</n1:password>
                             </n1:login>
                         </env:Body>
                     </env:Envelope>''' % (self.sfUserId, self.sfPassword, self.sfUserToken) 
        
        response = self._post_to_sf_api(self.SF_LOGIN_SERVER_URL, self.SF_LOGIN_ENDPOINT, payload, 'text/xml', 'login')
        
        sessionId = None
        serverUrl = None
    
        dom = xml.dom.minidom.parseString(response)
        if dom.getElementsByTagName('sessionId'):
            sessionId = dom.getElementsByTagName('sessionId').item(0).firstChild.nodeValue
        if dom.getElementsByTagName('serverUrl'):
            serverUrl = urlparse(dom.getElementsByTagName('serverUrl').item(0).firstChild.nodeValue).netloc
         
        self.sfSessionId = sessionId
        self.sfServerUrl = serverUrl
        self.response = response 
        
        self.XML_DOM_DEF = '''<?xml version="1.0" encoding="utf-8" ?>'''
        self.XML_SOAP_ENV = '''<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:urn="urn:enterprise.soap.sforce.com" xmlns:urn1="urn:sobject.enterprise.soap.sforce.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'''
        self.XML_SOAP_HEAD = '''<soapenv:Header>
                                    <urn:SessionHeader>
                                        <urn:sessionId>%s</urn:sessionId>
                                    </urn:SessionHeader>
                                </soapenv:Header>''' % self.sfSessionId

    
    #================================================================
    #    Create
    #----------------------------------------------------------------
    #    @param sfObject: The API Name of the object to be created
    #    @param sfFields: Dict of API Field Name:Value
    #
    #    @return: The Id of the object that was created
    #================================================================
    def create(self,sfObject,sfFields):     
        requestBody = '''<soapenv:Body>
                             <urn:create>
                                 <urn:sObjects xsi:type="urn1:%s">''' % sfObject
        
        for sfFieldName, sfFieldValue in sfFields.iteritems():
            requestBody += '<%s>%s</%s>' % (sfFieldName, sfFieldValue, sfFieldName)
        
        requestBody += '''      </urn:sObjects>
                            </urn:create>
                        </soapenv:Body>'''
        
        payload = '%s%s%s%s</soapenv:Envelope>' % (self.XML_DOM_DEF, self.XML_SOAP_ENV, self.XML_SOAP_HEAD, requestBody)

        self.response = self._post_to_sf_api(self.sfServerUrl, self.SF_API_REQUEST_ENDPOINT, payload, 'text/xml', 'create')
        
        recordId = None
    
        dom = xml.dom.minidom.parseString(self.response)
        if dom.getElementsByTagName('id'):
            recordId = dom.getElementsByTagName('id').item(0).firstChild.nodeValue
        return recordId
        
    #================================================================
    #     Update
    #----------------------------------------------------------------
    #    @param sfObject: The API Name of the object to be created
    #    @param sfId: The ID of the object to be updated
    #    @param sfFields: Dict of API Field Name:Value 
    #================================================================
    def update(self, sfObject, sfId,sfFields):    
        requestBody = '''<soapenv:Body>
                             <urn:update>
                                 <urn:sObjects xsi:type="urn1:%s">
                                     <urn1:Id>%s</urn1:Id>''' % (sfObject, sfId)
        
        for sfFieldName, sfFieldValue in sfFields.iteritems():
            requestBody += '<urn1:%s>%s</urn1:%s>' % (sfFieldName, sfFieldValue, sfFieldName)
        
        requestBody += '''      </urn:sObjects>
                            </urn:update>
                        </soapenv:Body>'''
        
        payload = '%s%s%s%s</soapenv:Envelope>' % (self.XML_DOM_DEF, self.XML_SOAP_ENV, self.XML_SOAP_HEAD, requestBody)

        self.response = self._post_to_sf_api(self.sfServerUrl, self.SF_API_REQUEST_ENDPOINT, payload, 'text/xml', 'update')
    
    #================================================================
    #    Delete
    #----------------------------------------------------------------
    #    @param sfId: The ID of the object to be deleted
    #================================================================ 
    def delete(self,sfId):   
        requestBody = '''<soapenv:Body>
                             <urn:delete>
                                 <urn:Ids>%s</urn:Ids>
                             </urn:delete>
                         </soapenv:Body>''' % sfId
        
        payload = '%s%s%s%s</soapenv:Envelope>' % (self.XML_DOM_DEF, self.XML_SOAP_ENV, self.XML_SOAP_HEAD, requestBody)

        self.response = self._post_to_sf_api(self.sfServerUrl, self.SF_API_REQUEST_ENDPOINT, payload, 'text/xml', 'delete')
    
    #================================================================
    #    Query
    #----------------------------------------------------------------
    #    @param sfQuery: The SOQL query to be executed
    #
    #    @return: Set of dicts containing API Field Name: Value from
    #             the query
    #================================================================
    def query(self,sfQuery):
        requestBody = '''<soapenv:Body>
                             <urn:query>
                                 <urn:queryString>%s</urn:queryString>
                             </urn:query>
                         </soapenv:Body>''' % sfQuery
                         
        payload = '%s%s%s%s</soapenv:Envelope>' % (self.XML_DOM_DEF, self.XML_SOAP_ENV, self.XML_SOAP_HEAD, requestBody)
        
        self.response = self._post_to_sf_api(self.sfServerUrl, self.SF_API_REQUEST_ENDPOINT, payload, 'text/xml', '""')
        
        dom = xml.dom.minidom.parseString(self.response)
        results = dom.getElementsByTagName('result')

        for result in results:
            resultrecords = []
            records = result.getElementsByTagName('records')
            for record in records:
                recordFields = {}
                for node in record.childNodes:
                    recordFields.update({string.replace(node.nodeName,"sf:",""):node.firstChild.nodeValue})
                resultrecords.append(recordFields)    
        
        return resultrecords
    
    #================================================================
    #    Post To SF API
    #----------------------------------------------------------------
    #    @param sfServerUrl: The domain to post to
    #    @param sfEndpoint: The API endpoint to post to
    #    @param payload: The content to post
    #    @param payloadContentType: The content type of the payload
    #    @param soapAction: The value to use for the SOAPAction header
    #
    #    @return: The response from the API
    #
    #    @raise APIError: Exception raised when API responds with 
    #                     an error message
    #
    #    @raise HTTPError: Exception raised when call to API responds
    #                      with an HTTP error code and no API output
    #================================================================
    def _post_to_sf_api(self, sfServerUrl, sfEndpoint, payload, payloadContentType, soapAction):
        
        self.payload = payload
        webservice = httplib.HTTPSConnection(sfServerUrl)
        webservice.putrequest("POST", sfEndpoint)
        webservice.putheader("Host", sfServerUrl)
        webservice.putheader("Content-Type", payloadContentType + "; charset=\"UTF-8\"")
        webservice.putheader("Content-length", "%d" % len(payload))
        webservice.putheader("SOAPAction", soapAction)
        webservice.endheaders()
        webservice.send(payload)
        webresponse = webservice.getresponse()
        response = webresponse.read()
        
        dom = xml.dom.minidom.parseString(response)
        if dom.getElementsByTagName('faultstring'):
            errorMsg = dom.getElementsByTagName('faultstring').item(0).firstChild.nodeValue
            raise APIError(errorMsg)
        
        if webresponse.status>=400:            
            raise HTTPError('Received HTTP Error')
        
        return response 
