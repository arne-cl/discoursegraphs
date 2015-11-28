<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:mmax="org.eml.MMAX2.discourse.MMAX2DiscourseLoader" xmlns:primmark="www.eml.org/NameSpaces/primmark" xmlns:secmark="www.eml.org/NameSpaces/secmark" xmlns:groups="www.eml.org/NameSpaces/groups" xmlns:sentence="www.eml.org/NameSpaces/sentence" version="1.0">
  <xsl:output method="text" indent="no" omit-xml-declaration="yes"/>
  <xsl:strip-space elements="*"/>
  <xsl:template match="words">
    <xsl:apply-templates/>
  </xsl:template>
  <xsl:template match="word">
    <xsl:value-of select="mmax:registerDiscourseElement(@id)"/>
    <xsl:apply-templates select="mmax:getStartedMarkables(@id)" mode="opening"/>
    <xsl:value-of select="mmax:setDiscourseElementStart()"/>
    <xsl:apply-templates/>
    <xsl:value-of select="mmax:setDiscourseElementEnd()"/>
    <xsl:apply-templates select="mmax:getEndedMarkables(@id)" mode="closing"/>
    <xsl:text> </xsl:text>
  </xsl:template>
  <xsl:template match="primmark:markable" mode="opening">
    <xsl:value-of select="mmax:startBold()"/>
    <xsl:value-of select="mmax:addLeftMarkableHandle(@mmax_level, @id, '[')"/>
    <xsl:value-of select="mmax:endBold()"/>
  </xsl:template>
  <xsl:template match="primmark:markable" mode="closing">
    <xsl:value-of select="mmax:startBold()"/>
    <xsl:value-of select="mmax:addRightMarkableHandle(@mmax_level, @id, ']')"/>
    <xsl:value-of select="mmax:endBold()"/>
  </xsl:template>
  <xsl:template match="secmark:markable" mode="opening">
    <xsl:value-of select="mmax:startBold()"/>
    <xsl:value-of select="mmax:addLeftMarkableHandle(@mmax_level, @id, '[')"/>
    <xsl:value-of select="mmax:endBold()"/>
  </xsl:template>
  <xsl:template match="secmark:markable" mode="closing">
    <xsl:value-of select="mmax:startBold()"/>
    <xsl:value-of select="mmax:addRightMarkableHandle(@mmax_level, @id, ']')"/>
    <xsl:value-of select="mmax:endBold()"/>
  </xsl:template>
  <xsl:template match="groups:markable" mode="opening">
    <xsl:value-of select="mmax:addLeftMarkableHandle(@mmax_level, @id, '(')"/>
  </xsl:template>
  <xsl:template match="groups:markable" mode="closing">
    <xsl:value-of select="mmax:addRightMarkableHandle(@mmax_level, @id, ')')"/>
  </xsl:template>
  <xsl:template match="sentence:markable" mode="opening">
</xsl:template>
  <xsl:template match="sentence:markable" mode="closing">
    <xsl:text>
</xsl:text>
  </xsl:template>
</xsl:stylesheet>
