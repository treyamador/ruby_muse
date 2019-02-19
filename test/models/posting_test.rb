require 'test_helper'

class PostingTest < ActiveSupport::TestCase
  def setup
    @posting = postings(:one)
  end

  test 'posting is valid' do
    assert @posting.valid?
  end

  test 'posting must have subject' do
    @posting.subject = '   '
    assert_not @posting.valid?
  end

  test 'posting must have content' do
    @posting.content = '   '
    assert_not @posting.valid?
  end

  test 'posting must have user id' do
    @posting.user_id = nil
    assert_not @posting.valid?
  end

  test 'posting subject has maximum of 100 chars ' do
    @posting.subject = 's' * 101
    assert_not @posting.valid?
  end

  test 'posting content has maximum of 5000 chars' do
    @posting.content = 't' * 5001
    assert_not @posting.valid?
  end
end
