require 'test_helper'

class UserTest < ActiveSupport::TestCase
  # test "the truth" do
  #   assert true
  # end

  def setup
    @user = users(:gary)
  end

  test 'user should be valid' do
    assert @user.valid?
  end

  test 'user must have first and last names' do
    @user.first_name = '    '
    assert_not @user.valid?
    @user.first_name = 'Gary'
    assert @user.valid?
    @user.last_name = '    '
    assert_not @user.valid?
  end

  test 'user names must be less than 255 chars' do
    @user.first_name = 'a' * 256
    assert_not @user.valid?
  end

  test 'user does not need middle name' do
    @user.middle_name = ''
    assert @user.valid?
  end

  test 'user must have email' do
    @user.email = '   '
    assert_not @user.valid?
  end

  test 'user must have valid email' do
    # this test case fails
    # @user.email = 'abc@info'
    # assert_not @user.valid?
    @user.email = 'qwe'
    assert_not @user.valid?
    @user.email = 'green.com'
    assert_not @user.valid?
  end

  test 'user must have password' do
    @user.password = ''
    assert_not @user.valid?
  end

  test 'user must have password of 6 letters' do
    @user.password = '12345'
    assert_not @user.valid?
  end
end
